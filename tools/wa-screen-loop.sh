#!/usr/bin/env bash
# wa-screen-loop.sh — the live board, at speed.
#
# A continuous runner for the single Discord board (tools/wa_screen.py): tick,
# breathe, repeat. Replaces the 60s StartInterval agent so the board updates
# near-instantly instead of once a minute.
#
#   StartInterval 60  →  this loop @ WA_INTERVAL (default 3s)
#
# Discord rate-limits message edits (~5 per 5s per channel), so the floor is a
# few seconds, not zero — too fast and the webhook gets 429'd. Override with:
#   WA_INTERVAL=5 tools/wa-screen-loop.sh
set -uo pipefail
cd "$(dirname "$0")/.."
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:$PATH"

INTERVAL="${WA_INTERVAL:-3}"

while true; do
  /bin/bash tools/wa-screen.sh >/dev/null 2>&1 || true
  sleep "$INTERVAL"
done
