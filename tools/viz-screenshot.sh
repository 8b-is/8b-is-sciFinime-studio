#!/bin/bash
# viz.vaked.dev — periodic screen → Discord + WhatsApp + kokoro voice
#
# Captures the M1 MacBook's screen (the Safari · viz.vaked.dev view is the
# important one) and broadcasts it:
#   - HF bucket: the recording is persisted (PeetPedro/viz-vaked-recordings,
#     private dataset, screens/…)
#   - Discord  : the image, via wa-stream (push --attach)
#   - WhatsApp : a text note, via the wa-stream replay inbox (replay.txt)
#   - kokoro   : a spoken line, locally (am_echo, the announcement voice)
# Scheduled by launchd every 4 hours (see ~/Library/LaunchAgents/).
#
# Guardrails — pings Discord instead of silently dropping when:
#   - the screen is locked (the lock screen is not viz.vaked.dev)
#   - Screen Recording permission is missing (screencapture can't see the display)
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
ERR="/tmp/viz-screen-err.txt"
TS="$(date '+%Y-%m-%d %H:%M %Z')"
POST=1
[[ "${1:-}" == "--no-post" ]] && POST=0

cleanup() { rm -f "$SHOT" "$ERR"; }
trap cleanup EXIT

cd "$STUDIO"

if [[ $POST -eq 1 ]]; then
  # Screen locked? Ping and stop — the lock screen is not viz.vaked.dev.
  LOCKED="$(uv run --script tools/screen-locked.py 2>/dev/null || echo 0)"
  if [[ "$LOCKED" == "1" ]]; then
    uv run tools/wa_stream.py push "" \
      --title "viz.vaked.dev — screen locked" \
      --footer "M1 MacBook · $TS · UltraCrushLove<3" \
      --color "#ff6432"
    exit 0
  fi
fi

# Capture (silent). Permission failure lands a ping, not a silent drop.
if ! screencapture -x "$SHOT" 2>"$ERR"; then
  if [[ $POST -eq 1 ]]; then
    uv run tools/wa_stream.py push "" \
      --title "viz.vaked.dev — screen recording permission missing" \
      --footer "$(head -c 120 "$ERR") · M1 MacBook · $TS" \
      --color "#ff2a85"
  fi
  exit 0
fi

if [[ $POST -eq 0 ]]; then
  echo "captured: $SHOT (not posted)"
  exit 0
fi

# HF private bucket — the recording is persisted (recording-mode).
if command -v hf >/dev/null 2>&1; then
  hf upload PeetPedro/viz-vaked-recordings "$SHOT" \
    "screens/$(basename "$SHOT")" --repo-type dataset >/dev/null 2>&1 || true
fi

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
