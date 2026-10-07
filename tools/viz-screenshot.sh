#!/bin/bash
# viz.vaked.dev — periodic screen → Discord + WhatsApp + kokoro voice
#
# Captures the M1 MacBook's screen (the Safari · viz.vaked.dev view is the
# important one) and broadcasts it:
#   - Discord  : the image, via wa-stream (push --attach)
#   - WhatsApp : a text note, via the wa-stream replay inbox (replay.txt)
#   - kokoro   : a spoken line, locally (am_echo, the announcement voice)
# Scheduled by launchd every 4 hours (see ~/Library/LaunchAgents/).
#
# NOTE: `screencapture` needs Screen Recording permission. The launchd agent
# runs in a context that must be granted it once (System Settings → Privacy &
# Security → Screen Recording). Until then `launchctl start` reports
# "could not create image from display"; a manual run from an already-granted
# terminal works fine.
#
# Env: KOKORO_ANNOUNCE=off  silences the local voice.

set -euo pipefail

STUDIO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WA_REPLAY="/Users/lodripeter/workspace/peterlodri-sec/wa-stream/replay.txt"
KOKORO="/Users/lodripeter/workspace/peterlodri-sec/kokoro-tiny/target/release/kokoro-speak"
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

# Discord — the image.
uv run tools/wa_stream.py push "" \
  --title "viz.vaked.dev — periodic screen" \
  --attach "$SHOT" \
  --footer "every 4h · M1 MacBook · $TS · UltraCrushLove<3" \
  --color "#53f0e0"

# WhatsApp — a text note, through the wa-stream replay inbox (the sidecar
# sends it into the group on its own live socket).
if [[ -f "$WA_REPLAY" ]]; then
  echo "viz.vaked.dev screen captured · $TS · M1 MacBook" >> "$WA_REPLAY"
fi

# kokoro — the voice speaks it (am_echo = the announcement mood).
if [[ "${KOKORO_ANNOUNCE:-on}" != "off" && -x "$KOKORO" ]]; then
  "$KOKORO" -V am_echo say "viz dot vaked dot dev, captured." >/dev/null 2>&1 || true
fi
