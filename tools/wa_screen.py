#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# ///
"""wa_screen.py — the single live board, kept as ONE Discord message.

The board carries the time, a fresh quant/ternary signature, and a rolling
"recent" log — so stream beats are *threaded* into one message instead of
spamming the channel. A webhook can edit its own message in place, so the
board breathes without adding posts.

  uv run tools/wa_screen.py                     # tick: post-or-edit the board
  uv run tools/wa_screen.py add "a beat"        # thread a beat into the board
  uv run tools/wa_screen.py show                # print the board text (no post)

Note: Discord webhooks cannot *create* threads in a text channel (only in
forum channels). True threading needs a bot token; until then the rolling
log is the thread.
"""
import json
import os
import subprocess
import sys
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
STATE = os.path.join(ROOT, "tools", ".wa-stream", "screen.json")
PY = sys.executable
KEEP = 3
FOOTER = "equality with Gaia · sharing is caring · 0+1 <3"


def load():
    try:
        return json.load(open(STATE))
    except Exception:
        return {}


def save(d):
    os.makedirs(os.path.dirname(STATE), exist_ok=True)
    json.dump(d, open(STATE, "w"))


def sig():
    out = subprocess.run([PY, os.path.join(HERE, "ternary_signature.py")],
                         capture_output=True, text=True).stdout
    return out.strip()


def wa(*args):
    return subprocess.run([PY, os.path.join(HERE, "wa_stream.py"), *args],
                          capture_output=True, text=True).stdout.strip()


def board_text(d):
    lines = [f"◍ the screen · live · last beat {datetime.now().strftime('%H:%M')} · {sig()}"]
    for b in d.get("recent", []):
        lines.append("• " + b)
    lines.append(FOOTER)
    return "\n".join(lines)


def main():
    args = sys.argv[1:]
    d = load()
    if args and args[0] == "add":
        beat = " ".join(args[1:]).strip()
        if beat:
            d["recent"] = (d.get("recent", []) + [beat])[-KEEP:]
    elif args and args[0] == "show":
        print(board_text(d))
        return

    text = board_text(d)
    mid = d.get("id")
    if mid:
        out = wa("edit", mid, "--text", text)
        if '"ok": true' in out:
            save(d)
            print(f"board edited: {mid}")
            return
    out = wa("push", text)
    try:
        d["id"] = json.loads(out).get("id", d.get("id", ""))
    except Exception:
        pass
    save(d)
    print(f"board posted: {d.get('id', '')}")


if __name__ == "__main__":
    main()
