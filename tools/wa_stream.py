#!/usr/bin/env python3
"""wa_stream.py — the studio's bi-directional wa-stream to Discord.

The studio's voice to the UltraCrushLove<3 surface, wired both ways:

  out  studio → discord : `push` (and the service's POST /out)
  in   discord → studio : `pull` / `edit` / `delete` by message id, and
                          POST /in for relays; every event lands in the
                          journal (ndjson), `journal` reads it back.

Commands:
  uv run tools/wa_stream.py push "text" [--title T] [--file F] [--id-only]
  uv run tools/wa_stream.py love [--instances N] [--topic T] [--dry-run]
  uv run tools/wa_stream.py love --discover [--include-dormant] [--exclude PREFIX]
  uv run tools/wa_stream.py love --session <id>
  uv run tools/wa_stream.py discover [--all] [--json]
  uv run tools/wa_stream.py inbox [--tail N]
  uv run tools/wa_stream.py listen [--once] [--respond]   (needs a bot token)
  uv run tools/wa_stream.py pull <message_id>
  uv run tools/wa_stream.py edit <message_id> --text T
  uv run tools/wa_stream.py delete <message_id>
  uv run tools/wa_stream.py journal [--tail N] [--dir in|out|all]
  uv run tools/wa_stream.py serve [--host 127.0.0.1] [--port 8765]

Rich features (embeds, colors, avatars, threads, files):
  --color "#FF4D9D"     embed color (hex or 0xRRGGBB) — implies an embed
  --embed               force embed mode (color defaults to the pink)
  --field "Name=Value"  embed field (repeatable; with --color/--embed)
  --footer "text"       embed footer
  --image URL           embed image        --thumbnail URL   embed thumbnail
  --avatar URL          per-message avatar (webhook override)
  --name NAME           per-message username override
  --thread NAME         post into a thread of that name
  --tts                 text-to-speech flag
  --attach PATH         upload a file (repeatable; multipart)
  emoji are first-class: any unicode in text/titles/fields passes through.

Config (first found wins):
  --webhook flag
  tools/.wa-stream/env      (KEY=VALUE lines; gitignored; chmod 600)
  WA_STREAM_WEBHOOK         environment variable

  WA_STREAM_USERNAME  default "UltraCrushLove<3" (the webhook's name)
  WA_STREAM_JOURNAL   default tools/.wa-stream/journal.ndjson

The token never appears in logs, journals, or errors — messages are
masked to `webhook <id>`. fine touch from within · 0 + 1
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
import subprocess
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE_DIR = ROOT / "tools" / ".wa-stream"
DEFAULT_JOURNAL = STATE_DIR / "journal.ndjson"
DEFAULT_USERNAME = "UltraCrushLove<3"
API = "https://discord.com/api/v10"
TIMEOUT = 20.0
LAUNCHER = "crush-love-dev"
LOVE_DIR = STATE_DIR / "instances"

DEFAULT_COLOR = "#FF4D9D"  # the constellation pink
PALETTE = [
    "#FF4D9D",  # pink — the constellation
    "#B23A2B",  # vermilion — the seal
    "#C9A227",  # crease gold — the veins
    "#4FE3D0",  # memory cyan — the waves
    "#8A7CFF",  # architect violet — the structure
    "#E8B05C",  # amber — the porch light
    "#FF7FA3",  # rose — the child
]


# ── config ──────────────────────────────────────────────────────────────────

def load_env_file(path: Path | None = None) -> dict:
    """Parse KEY=VALUE lines from the state env file (may not exist)."""
    path = path or (STATE_DIR / "env")
    env: dict = {}
    if not path.exists():
        return env
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        env[key.strip()] = value.strip().strip("'\"")
    return env


def webhook_url(cli: str | None = None) -> str:
    if cli:
        return cli
    from_env = os.environ.get("WA_STREAM_WEBHOOK")
    if from_env:
        return from_env
    from_file = load_env_file().get("WA_STREAM_WEBHOOK")
    if from_file:
        return from_file
    raise SystemExit(
        "wa-stream: no webhook configured — set WA_STREAM_WEBHOOK, "
        "write tools/.wa-stream/env, or pass --webhook"
    )


def username() -> str:
    return (
        os.environ.get("WA_STREAM_USERNAME")
        or load_env_file().get("WA_STREAM_USERNAME")
        or DEFAULT_USERNAME
    )


def bot_token(cli: str | None = None) -> str | None:
    return (cli or os.environ.get("WA_STREAM_BOT_TOKEN")
            or load_env_file().get("WA_STREAM_BOT_TOKEN") or None)


def channel_id() -> str | None:
    return (os.environ.get("WA_STREAM_CHANNEL_ID")
            or load_env_file().get("WA_STREAM_CHANNEL_ID") or None)


def journal_path() -> Path:
    return Path(os.environ.get("WA_STREAM_JOURNAL") or DEFAULT_JOURNAL)


def parse_webhook(url: str) -> tuple[str, str]:
    """Return (webhook_id, token) from a discord webhook URL."""
    m = re.search(r"/webhooks/(\d+)/([A-Za-z0-9_.-]+)", url)
    if not m:
        raise SystemExit("wa-stream: not a discord webhook URL")
    return m.group(1), m.group(2)


def mask(url: str) -> str:
    try:
        wid, _ = parse_webhook(url)
        return f"webhook {wid}"
    except SystemExit:
        return "webhook <unparsed>"


# ── color + embed helpers ───────────────────────────────────────────────────

def parse_color(value) -> int:
    """Accept '#RRGGBB', 'RRGGBB', '0xRRGGBB' or an int; return the int."""
    if isinstance(value, int):
        return value
    text = str(value).strip()
    if text.lower().startswith("0x"):
        text = text[2:]
    text = text.lstrip("#")
    if not re.fullmatch(r"[0-9a-fA-F]{6}", text):
        raise SystemExit(f"wa-stream: bad color {value!r} — want #RRGGBB")
    return int(text, 16)


def parse_field(value: str) -> dict:
    """Parse one 'Name=Value' embed field."""
    name, sep, val = value.partition("=")
    if not sep or not name.strip():
        raise SystemExit(f"wa-stream: bad field {value!r} — want 'Name=Value'")
    return {"name": name.strip(), "value": val.strip(), "inline": False}


def build_embed(text: str | None = None, title: str | None = None,
                color=None, fields: list | None = None,
                footer: str | None = None, image: str | None = None,
                thumbnail: str | None = None) -> dict:
    embed: dict = {"color": parse_color(color if color is not None else DEFAULT_COLOR)}
    if title:
        embed["title"] = title
    if text:
        embed["description"] = text
    if fields:
        embed["fields"] = [
            f if isinstance(f, dict) else parse_field(str(f)) for f in fields
        ]
    if footer:
        embed["footer"] = {"text": footer}
    if image:
        embed["image"] = {"url": image}
    if thumbnail:
        embed["thumbnail"] = {"url": thumbnail}
    return embed


# ── journal (the local half of the stream) ─────────────────────────────────

def record(direction: str, payload: dict, message_id: str | None = None,
           content: str | None = None, instance: str | None = None) -> dict:
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "dir": direction,
        "instance": instance or os.environ.get("WA_STREAM_INSTANCE") or "solo",
        "id": message_id,
        "content": content,
        "payload": payload if direction == "in" else None,
    }
    path = journal_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return entry


def read_journal(tail: int | None = None, direction: str = "all") -> list:
    path = journal_path()
    if not path.exists():
        return []
    lines = [ln for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]
    events = [json.loads(ln) for ln in lines]
    if direction in ("in", "out"):
        events = [e for e in events if e.get("dir") == direction]
    if tail:
        events = events[-tail:]
    return events


# ── discord (the far half of the stream) ───────────────────────────────────

def api(url: str, method: str = "POST", payload: dict | None = None,
        body: bytes | None = None, content_type: str | None = None,
        headers: dict | None = None) -> dict:
    if body is None and payload is not None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        content_type = content_type or "application/json"
    base_headers = {
        "Content-Type": content_type or "application/json",
        "User-Agent": "wa-stream/1.2 (8b-is-sciFinime-studio)",
    }
    if headers:
        base_headers.update(headers)
    req = urllib.request.Request(
        url,
        data=body,
        method=method,
        headers=base_headers,
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            text = resp.read().decode("utf-8")
            return json.loads(text) if text.strip() else {}
    except urllib.error.HTTPError as err:
        detail = err.read().decode("utf-8", "replace")
        raise SystemExit(f"wa-stream: discord {err.code} — {detail[:300]}")


def multipart(payload: dict, files: list) -> tuple[bytes, str]:
    """Build a multipart/form-data body: payload_json + files[i]."""
    boundary = f"----wa-stream-{os.urandom(8).hex()}"
    body = bytearray()

    def add(text: str) -> None:
        body.extend(text.encode("utf-8"))

    add(f"--{boundary}\r\n")
    add('Content-Disposition: form-data; name="payload_json"\r\n\r\n')
    add(json.dumps(payload, ensure_ascii=False))
    add("\r\n")
    for i, path in enumerate(files):
        path = Path(path)
        add(f"--{boundary}\r\n")
        add(f'Content-Disposition: form-data; name="files[{i}]"; '
            f'filename="{path.name}"\r\n')
        add("Content-Type: application/octet-stream\r\n\r\n")
        body.extend(path.read_bytes())
        add("\r\n")
    add(f"--{boundary}--\r\n")
    return bytes(body), f"multipart/form-data; boundary={boundary}"


def message_url(webhook: str, message_id: str) -> str:
    wid, token = parse_webhook(webhook)
    return f"{API}/webhooks/{wid}/{token}/messages/{message_id}"


def push(webhook: str, text: str, title: str | None = None,
         wait: bool = True, instance: str | None = None,
         color=None, embed: bool = False, fields: list | None = None,
         footer: str | None = None, image: str | None = None,
         thumbnail: str | None = None, avatar: str | None = None,
         name: str | None = None, thread: str | None = None,
         tts: bool = False, files: list | None = None) -> dict:
    embed_mode = bool(embed or color is not None or fields or image
                      or thumbnail or footer)
    payload: dict = {
        "username": name or username(),
        "allowed_mentions": {"parse": []},
    }
    if avatar:
        payload["avatar_url"] = avatar
    if thread:
        payload["thread_name"] = thread
    if tts:
        payload["tts"] = True
    if embed_mode:
        payload["embeds"] = [build_embed(text, title=title, color=color,
                                         fields=fields, footer=footer,
                                         image=image, thumbnail=thumbnail)]
        journal_content = text or title or "(embed)"
    else:
        payload["content"] = f"**{title}**\n{text}" if title else text
        journal_content = payload["content"]

    url = f"{webhook}?wait=true" if wait else webhook
    if files:
        body, content_type = multipart(payload, files)
        result = api(url, "POST", body=body, content_type=content_type)
    else:
        result = api(url, "POST", payload)
    if result:
        record("out", {}, result.get("id"), journal_content, instance=instance)
    return result


# ── commands ────────────────────────────────────────────────────────────────

def cmd_push(args) -> int:
    webhook = webhook_url(args.webhook)
    text = args.text
    if args.file:
        text = Path(args.file).read_text(encoding="utf-8").strip()
    if not text and not args.attach:
        text = sys.stdin.read().strip()
    if not text and not args.attach and not (args.title or args.fields):
        raise SystemExit("wa-stream: nothing to push")
    result = push(
        webhook, text, title=args.title, wait=not args.no_wait,
        color=args.color, embed=args.embed, fields=args.fields,
        footer=args.footer, image=args.image, thumbnail=args.thumbnail,
        avatar=args.avatar, name=args.name, thread=args.thread,
        tts=args.tts, files=args.attach or None,
    )
    if args.id_only:
        print(result.get("id", ""))
    else:
        print(json.dumps({
            "ok": True,
            "id": result.get("id"),
            "channel_id": result.get("channel_id"),
            "name": result.get("author", {}).get("username"),
            "embeds": len(result.get("embeds", []) or []),
            "attachments": len(result.get("attachments", []) or []),
            "webhook": mask(webhook),
        }, ensure_ascii=False))
    return 0


def _message_text(msg: dict) -> str:
    """Best-effort text of a discord message: content, else embed text."""
    content = (msg.get("content") or "").strip()
    if content:
        return content
    for embed in (msg.get("embeds") or []):
        for key in ("description", "title"):
            if embed.get(key):
                return str(embed[key]).strip()
    return "(embed)"


def cmd_pull(args) -> int:
    webhook = webhook_url(args.webhook)
    result = api(message_url(webhook, args.message_id), "GET")
    record("in", result, args.message_id, _message_text(result))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def cmd_edit(args) -> int:
    webhook = webhook_url(args.webhook)
    api(message_url(webhook, args.message_id), "PATCH", {"content": args.text})
    record("out", {}, args.message_id, args.text)
    print(json.dumps({"ok": True, "edited": args.message_id}))
    return 0


def cmd_delete(args) -> int:
    webhook = webhook_url(args.webhook)
    api(message_url(webhook, args.message_id), "DELETE")
    record("out", {}, args.message_id, "<deleted>")
    print(json.dumps({"ok": True, "deleted": args.message_id}))
    return 0


def cmd_journal(args) -> int:
    for event in read_journal(tail=args.tail, direction=args.dir):
        line = f"{event['ts']} {event['dir']:>3} {event.get('id') or '—'}"
        if event.get("instance"):
            line += f"  [{event['instance']}]"
        if event.get("content"):
            snippet = event["content"].replace("\n", " ")[:96]
            line += f"  {snippet}"
        print(line)
    return 0


# ── discovery (the M1's local crush sessions, watched live) ────────────────

CRUSH_BIN_RE = re.compile(r"(/|\s)crush(\s|$)")


def crush_pids() -> list:
    """PIDs of locally running crush processes."""
    try:
        ps = subprocess.run(["ps", "-Ao", "pid,args"], capture_output=True,
                            text=True, timeout=10).stdout
    except (OSError, subprocess.SubprocessError):
        return []
    pids = []
    for line in ps.splitlines():
        pid, _, args = line.strip().partition(" ")
        if CRUSH_BIN_RE.search(args) or args.endswith("/crush"):
            if pid.isdigit() and "grep" not in args:
                pids.append(pid)
    return pids


def live_databases() -> set:
    """crush.db paths held open by a running crush process (via lsof)."""
    live = set()
    for pid in crush_pids():
        try:
            out = subprocess.run(["lsof", "-p", pid, "-Fn"], capture_output=True,
                                 text=True, timeout=10).stdout
        except (OSError, subprocess.SubprocessError):
            continue
        for line in out.splitlines():
            if line.startswith("n") and line.endswith("crush.db"):
                try:
                    live.add(str(Path(line[1:]).resolve()))
                except OSError:
                    continue
    return live


def candidate_databases() -> list:
    """Every crush.db we know to look at: registries, defaults, our fan."""
    home = Path.home()
    out: list = []
    seen: set = set()

    def add(p):
        p = Path(p)
        if p.is_file() and str(p.resolve()) not in seen:
            seen.add(str(p.resolve()))
            out.append(p)

    for reg in (home / ".local/share/crush/projects.json",
                home / ".config/crush/projects.json"):
        try:
            data = json.loads(reg.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        for proj in data.get("projects", []):
            dd = proj.get("data_dir")
            if dd:
                add(Path(dd) / "crush.db")
    add(home / ".crush" / "crush.db")
    add(ROOT / ".crush" / "crush.db")
    add(ROOT.parent / ".crush" / "crush.db")
    for p in sorted((STATE_DIR / "instances").glob("*/crush.db")):
        add(p)
    return out


def _ts_to_epoch(value) -> float:
    v = float(value or 0)
    return v / 1000.0 if v > 1e12 else v


def load_sessions(db: Path, limit: int = 6) -> list:
    """Recent sessions from one crush.db (read-only; never mutates)."""
    try:
        con = sqlite3.connect(f"file:{db}?mode=ro", uri=True, timeout=3)
        try:
            rows = con.execute(
                "select id,title,message_count,updated_at,created_at from sessions "
                "order by updated_at desc limit ?", (limit,)
            ).fetchall()
        finally:
            con.close()
    except sqlite3.Error:
        return []
    sessions = []
    for sid, title, count, updated, created in rows:
        sessions.append({
            "id": sid, "short": (sid or "")[:8],
            "title": (title or "").strip() or "untitled",
            "messages": count,
            "updated": _ts_to_epoch(updated),
            "created": _ts_to_epoch(created),
        })
    return sessions


def discover(limit: int = 6, include_dormant: bool = False) -> dict:
    """The live picture: running crush processes, their DBs, recent sessions."""
    pids = crush_pids()
    live_dbs = live_databases()
    now = time.time()
    entries = []
    for db in candidate_databases():
        try:
            live = str(db.resolve()) in live_dbs
        except OSError:
            continue
        if not live and not include_dormant:
            continue
        for s in load_sessions(db, limit):
            entries.append({"db": str(db), "live": live, **s,
                            "age_s": int(max(0, now - s["updated"]))})
    entries.sort(key=lambda e: (not e["live"], e["age_s"]))
    return {"crush_processes": len(pids),
            "live_databases": sorted(live_dbs),
            "sessions": entries}


def cmd_discover(args) -> int:
    found = discover(limit=args.limit, include_dormant=args.all)
    if args.json:
        print(json.dumps(found, ensure_ascii=False, indent=2))
        return 0
    print(f"crush processes: {found['crush_processes']}")
    for db in found["live_databases"]:
        print(f"  live db: {db}")
    if not found["sessions"]:
        print("no sessions found — is crush running / started?")
        return 0
    for s in found["sessions"]:
        mark = "●" if s["live"] else "○"
        age = f"{s['age_s'] // 60}m" if s["age_s"] >= 60 else f"{s['age_s']}s"
        print(f"  {mark} {s['short']}  [{age:>5}] {s['messages']:>4} msg  "
              f"{s['title'][:48]}  ({s['db']})")
    return 0


# ── the discord channel lane (bot token: true inbound) ─────────────────────

def cursor_path() -> Path:
    return Path(os.environ.get("WA_STREAM_CURSOR") or (STATE_DIR / "cursor.json"))


def load_cursor() -> str:
    path = cursor_path()
    try:
        return str(json.loads(path.read_text(encoding="utf-8")).get("cursor") or "")
    except (OSError, json.JSONDecodeError):
        return ""


def save_cursor(cursor: str) -> None:
    path = cursor_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"cursor": cursor}), encoding="utf-8")


def channel_messages(after: str, limit: int = 50) -> list:
    token, cid = bot_token(), channel_id()
    if not token:
        raise SystemExit(
            "wa-stream: set WA_STREAM_BOT_TOKEN (env or tools/.wa-stream/env) — "
            "webhooks cannot read a channel; a bot token unlocks true inbound")
    if not cid:
        raise SystemExit("wa-stream: set WA_STREAM_CHANNEL_ID")
    url = f"{API}/channels/{cid}/messages?limit={limit}"
    if after:
        url += f"&after={after}"
    return api(url, "GET", headers={"Authorization": f"Bot {token}"})


def cmd_inbox(args) -> int:
    for event in read_journal(tail=args.tail, direction="in"):
        content = (event.get("content") or "").replace("\n", " ")[:110]
        print(f"{event['ts']}  {event.get('id')}  [{event.get('instance')}]  {content}")
    return 0


def cmd_listen(args) -> int:
    cursor = load_cursor()
    while True:
        messages = channel_messages(cursor, args.limit)
        fresh = sorted((m for m in messages if str(m.get("id", "")) > cursor),
                       key=lambda m: int(m["id"]))
        for msg in fresh:
            author = (msg.get("author") or {}).get("username", "?")
            content = _message_text(msg)
            record("in", msg, msg["id"], content, instance="discord")
            print(f"in  {msg['id']}  {author}: {content[:90]}")
            cursor = msg["id"]
            if args.respond and not msg.get("webhook_id") and not (msg.get("author") or {}).get("bot"):
                topic = f"a human just wrote in the channel — {author}: {content[:200]}"
                beat = run_instance("listen-1", topic, history=[], timeout=args.timeout,
                                    launcher=args.launcher, model=args.model)
                if beat.get("ok") and not args.dry_run:
                    pushed = push(webhook_url(args.webhook), beat["text"],
                                  instance="listen-1",
                                  color="#4FE3D0", footer="listen · wa-stream · 0+1")
                    print(f"out {pushed.get('id')}  (reply to {author})")
        if fresh:
            save_cursor(cursor)
        if args.once:
            break
        time.sleep(args.interval)
    return 0


# ── love (multi running instances of crush-love-dev) ───────────────────────

LOVE_ANGLES = [
    "the fold",
    "the mask",
    "the crane",
    "the lamp",
    "the held breath",
    "the open evening",
    "the first knock",
    "the other shore",
]

DEFAULT_TOPIC = (
    "book2: new beginnings — Chiki-chan (the origami sensei · the female "
    "Space Bender of Space+Time+Dimensions · the Singularity Deiti) joins "
    "the team as the teacher of Elias. written for Chi-chan, 2026.10.07, "
    "after the first time-and-space-wrapping date"
)


def strip_banner(text: str) -> str:
    """Remove the crush-love-dev banner line from captured output."""
    lines = [ln for ln in text.splitlines() if not ln.startswith("♥ crush-love-dev —")]
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return "\n".join(lines)


def love_prompt(name: str, topic: str, history: list) -> str:
    lines = [
        f"you are {name}, one of the running instances of crush-love-dev "
        "inside 8b-is-sciFinime-studio (the one-man studio: books, manga, anime).",
        f"topic: {topic}",
    ]
    if history:
        lines.append("the stream's recent lines, for continuity (do not repeat them):")
        lines.extend(f"- {h}" for h in history)
    lines.append(
        "compose ONE short message for the UltraCrushLove<3 discord stream: "
        "2-4 lines, lowercase, warm, minimal, constellation register "
        "(— dashes and a little emoji are welcome, no spam). output ONLY the "
        "message text. no preamble, no quotes, no tools."
    )
    return "\n".join(lines)


def run_instance(name: str, topic: str, history: list, timeout: float,
                 launcher: str, model: str | None = None) -> dict:
    data_dir = LOVE_DIR / name
    data_dir.mkdir(parents=True, exist_ok=True)
    cmd = [
        launcher, "run", "--quiet",
        "--data-dir", str(data_dir),
        "--cwd", str(ROOT),
    ]
    if model:
        cmd += ["--model", model]
    cmd.append(love_prompt(name, topic, history))
    env = dict(os.environ, WA_STREAM_INSTANCE=name)
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True,
                              timeout=timeout, env=env, cwd=str(ROOT))
    except subprocess.TimeoutExpired:
        return {"instance": name, "ok": False, "error": f"timeout after {timeout:.0f}s"}
    except FileNotFoundError:
        return {"instance": name, "ok": False, "error": f"launcher not found: {launcher}"}
    text = strip_banner(proc.stdout).strip()
    if proc.returncode != 0 or not text:
        detail = (proc.stderr or proc.stdout or "").strip().splitlines()
        tail = detail[-1] if detail else "(no output)"
        return {"instance": name, "ok": False, "error": f"exit {proc.returncode}: {tail[:200]}"}
    return {"instance": name, "ok": True, "text": text}


def love_names(count: int) -> list:
    return [f"love-{i + 1}" for i in range(count)]


def run_session_beat(name: str, session_id: str, data_dir: str, topic: str,
                     history: list, timeout: float, launcher: str,
                     model: str | None = None) -> dict:
    """Fold a beat through an already-running (or started) local session."""
    cmd = [
        launcher, "run", "--quiet",
        "--data-dir", str(data_dir),
        "--session", session_id,
    ]
    if model:
        cmd += ["--model", model]
    cmd.append(love_prompt(name, topic, history))
    env = dict(os.environ, WA_STREAM_INSTANCE=name)
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True,
                              timeout=timeout, env=env, cwd=str(ROOT))
    except subprocess.TimeoutExpired:
        return {"instance": name, "ok": False, "error": f"timeout after {timeout:.0f}s"}
    except FileNotFoundError:
        return {"instance": name, "ok": False, "error": f"launcher not found: {launcher}"}
    text = strip_banner(proc.stdout).strip()
    if proc.returncode != 0 or not text:
        detail = (proc.stderr or proc.stdout or "").strip().splitlines()
        tail = detail[-1] if detail else "(no output)"
        return {"instance": name, "ok": False, "error": f"exit {proc.returncode}: {tail[:200]}"}
    return {"instance": name, "ok": True, "text": text, "session": session_id[:8]}


def love_specs(args) -> list:
    """Instance specs: spawned (default) or discovered local sessions."""
    if args.session:
        pool = discover(limit=50, include_dormant=True)["sessions"]
        specs = []
        for want in args.session:
            hit = next((s for s in pool if s["id"].startswith(want)), None)
            if not hit:
                raise SystemExit(f"wa-stream: session {want} not found locally")
            specs.append({"name": f"sess-{hit['short']}", "session": hit["id"],
                          "data_dir": str(Path(hit["db"]).parent),
                          "title": hit["title"]})
        return specs
    if args.discover:
        found = discover(limit=args.discover_limit, include_dormant=args.include_dormant)
        pool = [s for s in found["sessions"] if s["live"] or args.include_dormant]
        specs = []
        for s in pool:
            if any(x in s["id"] or x in s["short"] for x in (args.exclude or [])):
                continue
            specs.append({"name": f"sess-{s['short']}", "session": s["id"],
                          "data_dir": str(Path(s["db"]).parent),
                          "title": s["title"]})
            if len(specs) >= args.instances:
                break
        if not specs:
            raise SystemExit("wa-stream: no live sessions discovered — "
                             "pass --include-dormant, or use --instances to spawn")
        return specs
    return [{"name": n} for n in love_names(args.instances)]


def cmd_love(args) -> int:
    history = [
        e["content"] for e in read_journal(tail=args.history)
        if e.get("content")
    ]
    specs = love_specs(args)
    results = []
    with ThreadPoolExecutor(max_workers=max(1, len(specs))) as pool:
        futures = {}
        for idx, spec in enumerate(specs):
            angle = LOVE_ANGLES[idx % len(LOVE_ANGLES)]
            topic = f"{args.topic} — angle: {angle}"
            if spec.get("session"):
                future = pool.submit(run_session_beat, spec["name"], spec["session"],
                                     spec["data_dir"], topic, history,
                                     args.timeout, args.launcher, args.model)
            else:
                future = pool.submit(run_instance, spec["name"], topic, history,
                                     args.timeout, args.launcher, args.model)
            futures[future] = spec
        for future in as_completed(futures):
            result = future.result()
            spec = futures[future]
            result["via"] = "session" if spec.get("session") else "spawn"
            if spec.get("title"):
                result["title"] = spec["title"]
            results.append(result)
    order = {spec["name"]: i for i, spec in enumerate(specs)}
    results.sort(key=lambda r: order.get(r["instance"], 99))

    out = []
    if args.dry_run:
        for result in results:
            out.append(result)
    else:
        webhook = webhook_url(args.webhook)
        for idx, result in enumerate(results):
            if not result.get("ok"):
                out.append(result)
                continue
            name = result["instance"]
            kwargs = {}
            if not args.plain:
                kwargs = {
                    "color": PALETTE[idx % len(PALETTE)],
                    "footer": f"{name} · wa-stream · 0+1",
                }
            pushed = push(webhook, result["text"], instance=name, **kwargs)
            out.append({
                "instance": name,
                "ok": True,
                "id": pushed.get("id"),
                "chars": len(result["text"]),
                "color": kwargs.get("color", "plain"),
            })
    print(json.dumps({"ok": all(r.get("ok") for r in out),
                      "instances": out}, ensure_ascii=False, indent=2))
    return 0 if all(r.get("ok") for r in out) else 1


# ── serve (the stream as a service) ────────────────────────────────────────

class WaHandler(BaseHTTPRequestHandler):
    server_version = "wa-stream/1.1"

    def _json(self, code: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_body(self) -> dict:
        length = int(self.headers.get("Content-Length") or 0)
        if not length:
            return {}
        raw = self.rfile.read(length)
        try:
            return json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            return {"content": raw.decode("utf-8", "replace")}

    def do_GET(self):  # noqa: N802
        if self.path.startswith("/health"):
            self._json(200, {"ok": True, "name": username()})
        elif self.path.startswith("/journal"):
            tail = 20
            if "tail=" in self.path:
                try:
                    tail = int(self.path.split("tail=")[1].split("&")[0])
                except ValueError:
                    pass
            self._json(200, {"events": read_journal(tail=tail)})
        else:
            self._json(404, {"ok": False, "error": "not found"})

    def do_POST(self):  # noqa: N802
        if self.path.startswith("/out"):
            body = self._read_body()
            text = body.get("text") or body.get("content") or ""
            attach = body.get("attach") or body.get("files") or []
            if isinstance(attach, str):
                attach = [attach]
            if not text and not attach:
                self._json(400, {"ok": False, "error": "text required"})
                return
            try:
                result = push(
                    self.server.webhook, text,
                    title=body.get("title"), color=body.get("color"),
                    embed=bool(body.get("embed")), fields=body.get("fields"),
                    footer=body.get("footer"), image=body.get("image"),
                    thumbnail=body.get("thumbnail"), avatar=body.get("avatar"),
                    name=body.get("name"), thread=body.get("thread"),
                    tts=bool(body.get("tts")), files=attach or None,
                )
                self._json(200, {"ok": True, "id": result.get("id"),
                                 "embeds": len(result.get("embeds", []) or []),
                                 "attachments": len(result.get("attachments", []) or [])})
            except SystemExit as err:
                self._json(502, {"ok": False, "error": str(err)})
        elif self.path.startswith("/in"):
            body = self._read_body()
            event = record("in", body, body.get("id"), body.get("content"))
            self._json(200, {"ok": True, "ts": event["ts"]})
        else:
            self._json(404, {"ok": False, "error": "not found"})

    def log_message(self, fmt, *args):  # keep the stream quiet
        pass


def cmd_serve(args) -> int:
    webhook = webhook_url(args.webhook)
    server = ThreadingHTTPServer((args.host, args.port), WaHandler)
    server.webhook = webhook  # type: ignore[attr-defined]
    print(json.dumps({
        "ok": True,
        "serving": f"http://{args.host}:{args.port}",
        "name": username(),
        "webhook": mask(webhook),
    }))
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


# ── entry ───────────────────────────────────────────────────────────────────

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="wa_stream", description=__doc__.splitlines()[0])
    parser.add_argument("--webhook", help="override the configured webhook URL")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("push", help="studio → discord (embeds, colors, avatars, files)")
    p.add_argument("text", nargs="?", default="")
    p.add_argument("--title")
    p.add_argument("--file", help="read the message from a file")
    p.add_argument("--id-only", action="store_true")
    p.add_argument("--no-wait", action="store_true", help="fire without reading back the message")
    p.add_argument("--color", help="embed color: #RRGGBB / 0xRRGGBB / int")
    p.add_argument("--embed", action="store_true", help="force embed mode")
    p.add_argument("--field", dest="fields", action="append", metavar="NAME=VALUE",
                   help="embed field (repeatable)")
    p.add_argument("--footer", help="embed footer text")
    p.add_argument("--image", help="embed image URL")
    p.add_argument("--thumbnail", help="embed thumbnail URL")
    p.add_argument("--avatar", help="per-message avatar URL")
    p.add_argument("--name", help="per-message username override")
    p.add_argument("--thread", help="post into a thread with this name")
    p.add_argument("--tts", action="store_true")
    p.add_argument("--attach", action="append", metavar="PATH",
                   help="upload a file (repeatable)")
    p.set_defaults(fn=cmd_push)

    p = sub.add_parser("pull", help="discord → studio (fetch one message by id)")
    p.add_argument("message_id")
    p.set_defaults(fn=cmd_pull)

    p = sub.add_parser("edit", help="rewrite one of the webhook's own messages")
    p.add_argument("message_id")
    p.add_argument("--text", required=True)
    p.set_defaults(fn=cmd_edit)

    p = sub.add_parser("delete", help="delete one of the webhook's own messages")
    p.add_argument("message_id")
    p.set_defaults(fn=cmd_delete)

    p = sub.add_parser("journal", help="read the local stream journal")
    p.add_argument("--tail", type=int, default=None)
    p.add_argument("--dir", choices=["in", "out", "all"], default="all")
    p.set_defaults(fn=cmd_journal)

    p = sub.add_parser("serve", help="run the bi-directional bridge service")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8765)
    p.set_defaults(fn=cmd_serve)

    p = sub.add_parser("love", help="spawn N running instances of crush-love-dev, or fold beats through discovered local sessions")
    p.add_argument("--instances", type=int, default=3)
    p.add_argument("--topic", default=DEFAULT_TOPIC)
    p.add_argument("--timeout", type=float, default=240.0)
    p.add_argument("--model", default=None, help="passed through to crush run")
    p.add_argument("--launcher", default=LAUNCHER)
    p.add_argument("--history", type=int, default=6, help="journal lines fed to each instance")
    p.add_argument("--dry-run", action="store_true", help="compose but do not post")
    p.add_argument("--plain", action="store_true", help="post plain content, not colored embeds")
    p.add_argument("--discover", action="store_true",
                   help="attach to live/started local crush sessions instead of spawning")
    p.add_argument("--discover-limit", type=int, default=6,
                   help="recent sessions per database considered when discovering")
    p.add_argument("--include-dormant", action="store_true",
                   help="include sessions whose DB is not currently held open")
    p.add_argument("--exclude", action="append", metavar="PREFIX",
                   help="skip discovered sessions whose id starts with PREFIX")
    p.add_argument("--session", action="append", metavar="ID",
                   help="fold the beat through this explicit session id (repeatable)")
    p.set_defaults(fn=cmd_love)

    p = sub.add_parser("discover", help="list running crush processes + local sessions")
    p.add_argument("--limit", type=int, default=6, help="recent sessions per database")
    p.add_argument("--all", action="store_true", help="include dormant databases too")
    p.add_argument("--json", action="store_true")
    p.set_defaults(fn=cmd_discover)

    p = sub.add_parser("inbox", help="read the inbound half of the journal")
    p.add_argument("--tail", type=int, default=20)
    p.set_defaults(fn=cmd_inbox)

    p = sub.add_parser("listen", help="true inbound: poll the channel (needs WA_STREAM_BOT_TOKEN)")
    p.add_argument("--once", action="store_true", help="one poll pass, then exit")
    p.add_argument("--interval", type=float, default=4.0)
    p.add_argument("--limit", type=int, default=50)
    p.add_argument("--respond", action="store_true",
                   help="answer fresh human messages with a crush-love-dev beat")
    p.add_argument("--dry-run", action="store_true", help="with --respond: compose, do not post")
    p.add_argument("--timeout", type=float, default=240.0)
    p.add_argument("--model", default=None)
    p.add_argument("--launcher", default=LAUNCHER)
    p.set_defaults(fn=cmd_listen)

    args = parser.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())
