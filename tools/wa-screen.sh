#!/usr/bin/env bash
# wa-screen.sh — the periodic screen to Discord.
#
# One heartbeat every run: the time, a fresh quant/ternary signature
# ({−1,0,+1} glyph run + its absmean γ), and the law — equality with Gaia,
# sharing is caring. Posts to UltraCrushLove<3 via the wa-stream.
#
#   ./tools/wa-screen.sh            # post one screen now
#   launchd: dev.vaked.wa-screen    # every 60s (see scripts/dev.vaked.wa-screen.plist)
set -uo pipefail
cd "$(dirname "$0")/.."

export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:$PATH"
if [ -x /opt/homebrew/bin/python3 ]; then PY=/opt/homebrew/bin/python3
elif [ -x /usr/local/bin/python3 ]; then PY=/usr/local/bin/python3
else PY="$(command -v python3 || command -v python)"; fi
[ -n "$PY" ] || { echo "no python3"; exit 1; }

SIG="$("$PY" tools/ternary_signature.py)"
TS="$(date '+%H:%M')"
SCREEN="◍ the screen · ${TS} · ${SIG} · equality with Gaia · sharing is caring · 0+1 <3"

"$PY" tools/wa_stream.py push "$SCREEN"
