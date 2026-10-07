#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# ///
"""ternary_signature.py — a fresh quant/ternary signature, seeded per minute.

The constellation's signature is `{-1, 0, +1}`: this draws a glyph run from a
sha256 seed and reports its absmean γ — the same `γ = mean|W|` the ternary lane
quantizes with. stdlib only, deterministic: same seed → same signature.

  uv run tools/ternary_signature.py          # seeded by the current minute
  uv run tools/ternary_signature.py <seed>   # explicit seed
"""
import hashlib
import sys
import time

GLYPH = {0: "\u2212", 1: "0", 2: "+"}  # −, 0, +


def run(seed: str, n: int = 16):
    h = hashlib.sha256(seed.encode()).digest()[:n]
    glyphs = [GLYPH[b % 3] for b in h]
    weights = [(b % 3) - 1 for b in h]  # {-1, 0, +1}
    return glyphs, weights


def signature(seed: str) -> str:
    glyphs, weights = run(seed)
    gamma = sum(abs(w) for w in weights) / len(weights)
    return "{" + "".join(glyphs) + "} \u03b3=" + f"{gamma:.2f}"


if __name__ == "__main__":
    seed = sys.argv[1] if len(sys.argv) > 1 else str(int(time.time() // 60))
    print(signature(seed))
