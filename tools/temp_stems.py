#!/usr/bin/env python3
"""temp_stems.py — the animatic's temp sound, synthesized.

Generates the four stems animatic 01 asks for as honest, ears-pending
placeholders (mono 22.05 kHz, 16-bit — small enough to commit):

  four-four-122.wav   a deep-house loop that never resolves (8 bars)
  creek.wav           shaped noise + small plops — the one clean sound
  whine.wav           a pure dry harmonic, mixed-too-dry on purpose
  breath-strip.wav    in · hold · out, the act-three metronome

Run from the studio root:

  uv run tools/temp_stems.py [--out DIR]

The stems self-report (duration, peak, RMS, estimated pitch) — a branch
may be ranked, only a verified branch may be bound; the *ears* verify
last. NOT music: temps. Replace with recordings before anything ships:
the creek especially — it must be ONE clean field recording, always.
"""

from __future__ import annotations

import argparse
import math
import random
import struct
import wave
from pathlib import Path

SR = 22050
RNG = random.Random(20261006)


def write_wav(path: Path, samples: list[float]) -> None:
    peak = max(1e-9, max(abs(s) for s in samples))
    if peak > 0.98:  # normalize only if hot; keep intended dynamics
        samples = [s * (0.98 / peak) for s in samples]
    with wave.open(str(path), "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(b"".join(struct.pack("<h", int(max(-1, min(1, s)) * 32767)) for s in samples))


def report(path: Path, samples: list[float]) -> None:
    n = len(samples)
    peak = max(abs(s) for s in samples)
    rms = math.sqrt(sum(s * s for s in samples) / n)
    crossings = sum(1 for a, b in zip(samples, samples[1:]) if a <= 0 < b or a > 0 >= b)
    est_hz = crossings / 2 / (n / SR)
    print(
        f"  {path.name:22s} {n / SR:5.1f}s  peak {peak:4.2f}  rms {rms:5.3f}  "
        f"est. pitch {est_hz:6.1f} Hz"
    )


def env(t: float, attack: float, decay: float) -> float:
    a = min(1.0, t / attack) if attack > 0 else 1.0
    return a * math.exp(-max(0.0, t - attack) / decay)


def four_four(duration: float = 15.75, bpm: float = 122.0) -> list[float]:
    """Kick on the quarters, hats on the off-eighths, one soft bar-blip."""
    beat = 60.0 / bpm
    n = int(duration * SR)
    out = [0.0] * n
    for i in range(n):
        t = i / SR
        beat_pos = t / beat
        into = (beat_pos % 1.0) * beat  # seconds into the beat

        # kick: 55 Hz, punchy decay
        if into < 0.35:
            out[i] += 0.85 * env(into, 0.004, 0.11) * math.sin(2 * math.pi * 55 * into)
        # hat: off-eighths, short noise
        off = (beat_pos - 0.5) % 1.0 * beat
        if off < 0.05:
            out[i] += 0.15 * env(off, 0.001, 0.012) * (RNG.random() * 2 - 1)
        # bar blip: 220 Hz, barely there
        bar_pos = (t / (4 * beat)) % 1.0
        if bar_pos * 4 * beat < 0.4:
            out[i] += 0.08 * env(bar_pos * 4 * beat, 0.005, 0.15) * math.sin(2 * math.pi * 220 * t)

    # loop-friendly edges
    fade = int(0.05 * SR)
    for i in range(fade):
        g = i / fade
        out[i] *= g
        out[-1 - i] *= g
    return out


def creek(duration: float = 20.0) -> list[float]:
    """Shaped noise (a one-pole lowpass plus slow water swells) + plops."""
    n = int(duration * SR)
    out = [0.0] * n
    lp = 0.0
    lp2 = 0.0
    for i in range(n):
        t = i / SR
        white = RNG.random() * 2 - 1
        lp = lp + 0.22 * (white - lp)      # lowpassed noise: moving water
        lp2 = lp2 + 0.03 * (lp - lp2)      # deeper bed
        swell = 0.6 + 0.4 * math.sin(2 * math.pi * 0.13 * t) * math.sin(2 * math.pi * 0.045 * t + 1.1)
        out[i] = (lp * 0.22 + lp2 * 0.5) * swell

    # plops: tiny stone sounds, deterministic-random
    t = 0.8
    while t < duration - 0.5:
        start = int(t * SR)
        f = RNG.choice([420.0, 560.0, 700.0, 880.0])
        for k in range(int(0.09 * SR)):
            if start + k < n:
                tt = k / SR
                out[start + k] += 0.18 * env(tt, 0.002, 0.02) * math.sin(2 * math.pi * f * tt)
        t += RNG.uniform(1.4, 3.2)

    fade = int(0.4 * SR)
    for i in range(fade):
        g = i / fade
        out[i] *= g
        out[-1 - i] *= g
    return out


def whine(duration: float = 12.0, hz: float = 1568.0) -> list[float]:
    """One sustained harmonic, no reverb — pasted in from another film."""
    n = int(duration * SR)
    out = []
    for i in range(n):
        t = i / SR
        drift = 3.0 * math.sin(2 * math.pi * 0.07 * t)  # ±3 Hz, uncomfortably alive
        f = hz + drift
        out.append(0.24 * (math.sin(2 * math.pi * f * t) + 0.12 * math.sin(2 * math.pi * 2 * f * t)))
    fade = int(0.15 * SR)
    for i in range(fade):
        g = i / fade
        out[i] *= g
        out[-1 - i] *= g
    return out


def breath_strip(inhale: float = 3.0, hold: float = 3.0, exhale: float = 3.0) -> list[float]:
    n = int((inhale + hold + exhale) * SR)
    out = [0.0] * n
    lp = 0.0
    for i in range(n):
        t = i / SR
        white = RNG.random() * 2 - 1
        lp = lp + 0.25 * (white - lp)
        if t < inhale:                     # in: rising
            g = (t / inhale) ** 1.6
        elif t < inhale + hold:            # hold: nearly nothing
            g = 0.05
        else:                              # out: falling
            g = 0.85 * (1.0 - (t - inhale - hold) / exhale) ** 1.4
        out[i] = lp * g * 0.35
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Generate the animatic's temp stems")
    ap.add_argument("--out", default="projects/01.01-sandbox-in-the-shell/assets/sound/animatic-01-temp")
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)

    stems = {
        "four-four-122.wav": four_four(),
        "creek.wav": creek(),
        "whine.wav": whine(),
        "breath-strip.wav": breath_strip(),
    }
    print(f"temp stems → {out}")
    for name, samples in stems.items():
        path = out / name
        write_wav(path, samples)
        report(path, samples)
    print("temps only. the creek must become ONE clean recording; the ears verify last.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
