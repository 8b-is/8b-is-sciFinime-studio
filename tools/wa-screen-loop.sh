#!/usr/bin/env bash
# wa-screen-loop.sh - the live board, at speed.
#
# A continuous runner for the single Discord board (tools/wa_screen.py): tick,
# breathe, repeat. Replaces the retired 60s StartInterval agent so the board
# updates near-instantly instead of once a minute.
#
#   StartInterval 60  ->  this loop @ WA_INTERVAL (default 3s)
#
# Discord rate-limits message edits (~5 per 5s per channel), so the floor is a
# few seconds, not zero: too fast and the webhook gets 429'd. WA_INTERVAL is
# floored at 3s no matter what the environment asks for. Override with:
#   WA_INTERVAL=5 tools/wa-screen-loop.sh
set -uo pipefail

cd "$(dirname "$0")/.." || exit 1
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:$PATH"

# Numeric guard + floor: a bad, empty, or zero value must not become a busy loop.
INTERVAL="${WA_INTERVAL:-3}"
case "$INTERVAL" in (''|*[!0-9]*) INTERVAL=3 ;; esac
[ "$INTERVAL" -ge 3 ] || INTERVAL=3

# Per-tick ceiling: a stalled tick (network hang) must not freeze the board.
TIMEOUT="${WA_TIMEOUT:-30}"
case "$TIMEOUT" in (''|*[!0-9]*) TIMEOUT=30 ;; esac
[ "$TIMEOUT" -ge 1 ] || TIMEOUT=30

# Single-instance lock. mkdir is atomic and present on macOS, unlike flock; a
# second launch would otherwise double-edit the board.
LOCK="${TMPDIR:-/tmp}/wa-screen-loop.lock"
OUT="$(mktemp "${TMPDIR:-/tmp}/wa-screen-loop.XXXXXX")"
if ! mkdir "$LOCK" 2>/dev/null; then
  echo "wa-screen-loop: another instance holds $LOCK; exiting" >&2
  rm -f "$OUT"
  exit 0
fi
trap 'rmdir "$LOCK" 2>/dev/null; rm -f "$OUT"' EXIT INT TERM

# Failures are recorded, never swallowed, so a broken setup is visible.
LOG="tools/.wa-stream/loop.log"
mkdir -p "$(dirname "$LOG")"

run_once() {
  bash tools/wa-screen.sh >"$OUT" 2>&1 &
  local pid=$! guard
  ( sleep "$TIMEOUT"; kill "$pid" 2>/dev/null ) >/dev/null 2>&1 &
  guard=$!
  wait "$pid" 2>/dev/null
  local rc=$?
  kill "$guard" 2>/dev/null
  return "$rc"
}

while true; do
  run_once
  rc=$?
  if [ "$rc" -ne 0 ]; then
    printf '%s wa-screen.sh failed (rc=%s): %s\n' \
      "$(date -u +%FT%TZ)" "$rc" "$(tail -n1 "$OUT" 2>/dev/null)" >>"$LOG"
  fi
  sleep "$INTERVAL"
done
