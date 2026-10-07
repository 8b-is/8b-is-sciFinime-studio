#!/usr/bin/env bash
# wa-screen.sh — the single live board.
#
# ONE message in UltraCrushLove<3, edited in place every run (never re-posted):
# the current time + a fresh quant/ternary signature ({−1,0,+1} glyph run + its
# absmean γ). First run posts it and remembers the id; every later run PATCHes
# that same message. The law rides along: equality with Gaia · sharing is caring.
#
#   ./tools/wa-screen.sh            # post-or-edit the board now
#   launchd: dev.vaked.wa-screen    # every 60s (scripts/dev.vaked.wa-screen.plist)
set -uo pipefail
cd "$(dirname "$0")/.."

export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:$PATH"
if [ -x /opt/homebrew/bin/python3 ]; then PY=/opt/homebrew/bin/python3
elif [ -x /usr/local/bin/python3 ]; then PY=/usr/local/bin/python3
else PY="$(command -v python3 || command -v python)"; fi
[ -n "$PY" ] || { echo "no python3"; exit 1; }

STATE="tools/.wa-stream/screen.json"
mkdir -p "$(dirname "$STATE")"
MSG_ID="$("$PY" -c 'import json,sys
try: print(json.load(open(sys.argv[1])).get("id",""))
except Exception: print("")' "$STATE")"

SIG="$("$PY" tools/ternary_signature.py)"
TS="$(date '+%H:%M')"
BOARD="◍ the screen · live · last beat ${TS} · ${SIG}
equality with Gaia · sharing is caring · 0+1 <3"

if [ -n "$MSG_ID" ] && "$PY" tools/wa_stream.py edit "$MSG_ID" --text "$BOARD" >/dev/null 2>&1; then
  echo "board edited: $MSG_ID"
  exit 0
fi

OUT="$("$PY" tools/wa_stream.py push "$BOARD")"
NEW="$("$PY" -c 'import json,sys
try: print(json.loads(sys.argv[1]).get("id",""))
except Exception: print("")' "$OUT")"
if [ -n "$NEW" ]; then
  printf '{"id":"%s"}\n' "$NEW" > "$STATE"
  echo "board posted: $NEW"
else
  echo "board failed: $OUT" >&2
  exit 1
fi
