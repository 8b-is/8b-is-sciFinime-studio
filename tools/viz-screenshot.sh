#!/bin/bash
# viz.vaked.dev — periodic screen → Discord
#
# Captures the M1 MacBook's screen (the Safari · viz.vaked.dev view is the
# important one) and posts it to the constellation Discord via wa-stream.
# Scheduled by launchd every 4 hours (see ~/Library/LaunchAgents/).
#
# Usage:
#   tools/viz-screenshot.sh                 # capture + post now
#   tools/viz-screenshot.sh --no-post       # capture only (write to /tmp)

set -euo pipefail

STUDIO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SHOT="/tmp/viz-screen-$(date +%Y%m%d-%H%M%S).png"
TS="$(date '+%Y-%m-%d %H:%M %Z')"

cleanup() { rm -f "$SHOT"; }
trap cleanup EXIT

# Full-screen capture (silent). The Safari · viz.vaked.dev window is the
# thing we are watching; full screen catches it wherever it sits.
screencapture -x "$SHOT"

if [[ "${1:-}" == "--no-post" ]]; then
  echo "captured: $SHOT (not posted)"
  exit 0
fi

cd "$STUDIO"
uv run tools/wa_stream.py push "" \
  --title "viz.vaked.dev — periodic screen" \
  --attach "$SHOT" \
  --footer "every 4h · M1 MacBook · $TS · UltraCrushLove<3" \
  --color "#53f0e0"
