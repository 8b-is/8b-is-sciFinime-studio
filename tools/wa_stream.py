#!/usr/bin/env python3
"""wa_stream.py — the studio's bi-directional wa-stream to Discord.

The studio's voice to the UltraCrushLove<3 surface, wired both ways:

  out  studio → discord : `push` (and the service's POST /out)
  in   discord → studio : `pull` / `edit` / `delete` by message id, and
                          POST /in for relays; every event lands in the
                          journal (ndjson), `journal` reads it back.

Commands:
  uv run tools/wa_stream.py push "text" [--title T] [--file F] [--id-only]
  uv run tools/wa_stream.py pull <message_id>
  uv run tools/wa_stream.py edit <message_id> --text T
  uv run tools/wa_stream.py delete <message_id>
  uv run tools/wa_stream.py journal [--tail N] [--dir in|out|all]
  uv run tools/wa_stream.py serve [--host 127.0.0.1] [--port 8765]

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
import subprocess
import sys
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
    from_file = load_env_file().get("WA_STREAM_WEBHOOK")
    if from_file:
        return from_file
    from_env = os.environ.get("WA_STREAM_WEBHOOK")
    if from_env:
        return from_env
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

def api(url: str, method: str = "POST", payload: dict | None = None) -> dict:
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "wa-stream/1.0 (8b-is-sciFinime-studio)",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            body = resp.read().decode("utf-8")
            return json.loads(body) if body.strip() else {}
    except urllib.error.HTTPError as err:
        detail = err.read().decode("utf-8", "replace")
        raise SystemExit(f"wa-stream: discord {err.code} — {detail[:300]}")


def message_url(webhook: str, message_id: str) -> str:
    wid, token = parse_webhook(webhook)
    return f"{API}/webhooks/{wid}/{token}/messages/{message_id}"


def push(webhook: str, text: str, title: str | None = None,
         wait: bool = True, instance: str | None = None) -> dict:
    content = f"**{title}**\n{text}" if title else text
    payload = {
        "content": content,
        "username": username(),
        "allowed_mentions": {"parse": []},
    }
    result = api(f"{webhook}?wait=true" if wait else webhook, "POST", payload)
    if result:
        record("out", {}, result.get("id"), content, instance=instance)
    return result


# ── commands ────────────────────────────────────────────────────────────────

def cmd_push(args) -> int:
    webhook = webhook_url(args.webhook)
    text = args.text
    if args.file:
        text = Path(args.file).read_text(encoding="utf-8").strip()
    if not text:
        text = sys.stdin.read().strip()
    if not text:
        raise SystemExit("wa-stream: nothing to push")
    result = push(webhook, text, title=args.title, wait=not args.no_wait)
    if args.id_only:
        print(result.get("id", ""))
    else:
        print(json.dumps({
            "ok": True,
            "id": result.get("id"),
            "channel_id": result.get("channel_id"),
            "name": result.get("author", {}).get("username"),
            "webhook": mask(webhook),
        }, ensure_ascii=False))
    return 0


def cmd_pull(args) -> int:
    webhook = webhook_url(args.webhook)
    result = api(message_url(webhook, args.message_id), "GET")
    record("in", result, args.message_id, result.get("content"))
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


# ── serve (the stream as a service) ────────────────────────────────────────

class WaHandler(BaseHTTPRequestHandler):
    server_version = "wa-stream/1.0"

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
            if not text:
                self._json(400, {"ok": False, "error": "text required"})
                return
            try:
                result = push(self.server.webhook, text, title=body.get("title"))
                self._json(200, {"ok": True, "id": result.get("id")})
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
        "(— dashes fine, no emoji spam). output ONLY the message text. "
        "no preamble, no quotes, no tools."
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


def cmd_love(args) -> int:
    history = [
        e["content"] for e in read_journal(tail=args.history)
        if e.get("content")
    ]
    names = love_names(args.instances)
    results = []
    with ThreadPoolExecutor(max_workers=max(1, args.instances)) as pool:
        futures = {}
        for idx, name in enumerate(names):
            angle = LOVE_ANGLES[idx % len(LOVE_ANGLES)]
            topic = f"{args.topic} — angle: {angle}"
            futures[pool.submit(run_instance, name, topic, history,
                                args.timeout, args.launcher, args.model)] = name
        for future in as_completed(futures):
            results.append(future.result())
    results.sort(key=lambda r: names.index(r["instance"]))

    out = []
    if args.dry_run:
        for result in results:
            out.append(result)
    else:
        webhook = webhook_url(args.webhook)
        for result in results:
            if not result.get("ok"):
                out.append(result)
                continue
            pushed = push(webhook, result["text"], instance=result["instance"])
            out.append({
                "instance": result["instance"],
                "ok": True,
                "id": pushed.get("id"),
                "chars": len(result["text"]),
            })
    print(json.dumps({"ok": all(r.get("ok") for r in out),
                      "instances": out}, ensure_ascii=False, indent=2))
    return 0 if all(r.get("ok") for r in out) else 1


# ── entry ───────────────────────────────────────────────────────────────────

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="wa_stream", description=__doc__.splitlines()[0])
    parser.add_argument("--webhook", help="override the configured webhook URL")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("push", help="studio → discord")
    p.add_argument("text", nargs="?", default="")
    p.add_argument("--title")
    p.add_argument("--file", help="read the message from a file")
    p.add_argument("--id-only", action="store_true")
    p.add_argument("--no-wait", action="store_true", help="fire without reading back the message")
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

    p = sub.add_parser("love", help="spawn N running instances of crush-love-dev, each streaming a beat")
    p.add_argument("--instances", type=int, default=3)
    p.add_argument("--topic", default=DEFAULT_TOPIC)
    p.add_argument("--timeout", type=float, default=240.0)
    p.add_argument("--model", default=None, help="passed through to crush run")
    p.add_argument("--launcher", default=LAUNCHER)
    p.add_argument("--history", type=int, default=6, help="journal lines fed to each instance")
    p.add_argument("--dry-run", action="store_true", help="compose but do not post")
    p.set_defaults(fn=cmd_love)

    args = parser.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())
