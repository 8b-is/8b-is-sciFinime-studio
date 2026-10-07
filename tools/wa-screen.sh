#!/usr/bin/env bash
# wa-screen.sh — thin wrapper to the live board (tools/wa_screen.py).
#
# One message in UltraCrushLove<3, edited in place every run; beats are threaded
# into its rolling "recent" log instead of re-posting. Run every 60 s by the
# launchd agent dev.vaked.wa-screen (scripts/dev.vaked.wa-screen.plist).
#
#   ./tools/wa-screen.sh                 # tick the board (post first, then edit)
#   ./tools/wa-screen.sh add "a beat"    # thread a beat into the board
set -uo pipefail
cd "$(dirname "$0")/.."

export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:$PATH"
if [ -x /opt/homebrew/bin/python3 ]; then PY=/opt/homebrew/bin/python3
elif [ -x /usr/local/bin/python3 ]; then PY=/usr/local/bin/python3
else PY="$(command -v python3 || command -v python)"; fi
[ -n "$PY" ] || { echo "no python3"; exit 1; }

exec "$PY" tools/wa_screen.py "$@"
