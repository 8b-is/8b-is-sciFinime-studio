#!/usr/bin/env python3
"""listen_stems.py — the ears: measure the stems so the notes have numbers.

Reads mono/stereo PCM WAVs and reports, per file:

  meta        duration · sample rate · channels
  levels      peak / RMS dBFS · crest factor
  body        per-second RMS window (min / median / max)
  silence     runs ≥ 150 ms below -50 dBFS (count · longest)
  onsets      energy onsets → count · median interval → BPM estimate
  tone        estimated fundamental (autocorrelation) · tail ratio

Run from the studio root:

  uv run --with numpy tools/listen_stems.py [wav ...]

Defaults to the animatic 01 temp stems. The numbers here feed the
listening-pass notes; the *ears* still verify last — a branch may be
ranked, only a verified branch may be bound.
"""

from __future__ import annotations

import math
import sys
import wave
from pathlib import Path

import numpy as np

DEFAULT_DIR = Path("projects/01.01-sandbox-in-the-shell/assets/sound/animatic-01-temp")

SILENCE_DBFS = -50.0
SILENCE_MIN_S = 0.150
HOP_S = 0.010
ONSET_RATIO = 1.9          # short-window RMS must exceed local median by this
ONSET_MIN_GAP_S = 0.100
ONSET_FLOOR_DBFS = -45.0


def load(path: Path) -> tuple[np.ndarray, int]:
    with wave.open(str(path), "rb") as w:
        sr = w.getframerate()
        frames = w.readframes(w.getnframes())
        raw = np.frombuffer(frames, dtype="<i2").astype(np.float64) / 32768.0
        if w.getnchannels() == 2:
            raw = raw.reshape(-1, 2).mean(axis=1)
    return raw, sr


def dbfs(x: float) -> float:
    return -math.inf if x <= 0 else 20 * math.log10(x)


def windows(samples: np.ndarray, sr: int, hop_s: float = HOP_S) -> np.ndarray:
    hop = max(1, int(hop_s * sr))
    n = len(samples) // hop
    if n == 0:
        return np.zeros(1)
    trimmed = samples[: n * hop].reshape(n, hop)
    return np.sqrt((trimmed**2).mean(axis=1))


def silence_runs(rms: np.ndarray) -> tuple[int, float]:
    quiet = rms < 10 ** (SILENCE_DBFS / 20)
    runs, cur = [], 0
    for q in quiet:
        if q:
            cur += 1
        elif cur:
            runs.append(cur)
            cur = 0
    if cur:
        runs.append(cur)
    runs = [r for r in runs if r * HOP_S >= SILENCE_MIN_S]
    return len(runs), (max(runs) * HOP_S if runs else 0.0)


def onsets(rms: np.ndarray) -> list[int]:
    med = np.median(rms) if len(rms) else 0.0
    thr = max(med * ONSET_RATIO, 10 ** (ONSET_FLOOR_DBFS / 20))
    found, last = [], -10**9
    gap = int(ONSET_MIN_GAP_S / HOP_S)
    for i in range(1, len(rms) - 1):
        if rms[i] > thr and rms[i] >= rms[i - 1] and rms[i] > rms[i + 1]:
            if i - last >= gap:
                found.append(i)
            last = i
    return found


def fundamental(samples: np.ndarray, sr: int) -> tuple[float, float]:
    seg = samples
    if len(seg) > sr * 3:
        mid = len(seg) // 2
        seg = seg[mid - sr : mid + sr]
    seg = seg - seg.mean()
    if not np.any(seg):
        return 0.0, 0.0
    ac = np.correlate(seg, seg, mode="full")[len(seg) - 1 :]
    ac /= ac[0] if ac[0] else 1.0
    lo, hi = int(sr / 2200), int(sr / 40)
    if hi >= len(ac):
        return 0.0, 0.0
    best_lag, best = 0, 0.0
    for lag in range(lo, hi):
        if ac[lag] >= ac[lag - 1] and ac[lag] >= ac[lag + 1] and ac[lag] > best:
            best, best_lag = ac[lag], lag
    return (sr / best_lag, float(best)) if best_lag and best > 0.35 else (0.0, float(best))


def report(path: Path) -> None:
    x, sr = load(path)
    dur = len(x) / sr
    peak = float(np.max(np.abs(x))) if len(x) else 0.0
    rms = float(np.sqrt((x**2).mean())) if len(x) else 0.0
    per_sec = windows(x, sr, hop_s=1.0)
    sec_db = [dbfs(v) for v in per_sec]
    n_sil, longest_sil = silence_runs(windows(x, sr))
    ons = onsets(windows(x, sr))
    bpm = 0.0
    if len(ons) >= 5:
        gaps = np.diff(ons) * HOP_S
        bpm = 60.0 / float(np.median(gaps))
    freq, strength = fundamental(x, sr)
    tail = dbfs(float(np.sqrt((x[-int(0.2 * sr) :] ** 2).mean()))) - dbfs(rms)

    print(f"— {path.name}")
    print(f"  meta     {dur:6.2f}s · {sr} Hz · mono")
    print(f"  levels   peak {dbfs(peak):5.1f} dBFS · rms {dbfs(rms):5.1f} dBFS · crest {dbfs(peak) - dbfs(rms):4.1f} dB")
    print(f"  body     per-sec rms min {min(sec_db):5.1f} / med {dbfs(np.median(per_sec)):5.1f} / max {max(sec_db):5.1f} dBFS")
    print(f"  silence  {n_sil} runs ≥150ms · longest {longest_sil:4.2f}s")
    print(f"  onsets   {len(ons)} · interval med {1000 * HOP_S * (np.median(np.diff(ons)) if len(ons) > 1 else 0):6.1f} ms · rate≈{bpm:5.1f}/min")
    print(f"  tone     est {freq:7.1f} Hz (r={strength:4.2f}) · tail {tail:+5.1f} dB vs body")
    print()


def main() -> int:
    args = sys.argv[1:]
    files = [Path(a) for a in args] if args else sorted(DEFAULT_DIR.glob("*.wav"))
    if not files:
        print(f"no wavs found (looked in {DEFAULT_DIR})", file=sys.stderr)
        return 1
    for f in files:
        report(f)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
