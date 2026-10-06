#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["pillow"]
# ///
"""collect_plates.py — copy a run's plates from ComfyUI's output into the
studio repo as repo-friendly JPGs (commit picks, not raw runs).

  uv run tools/collect_plates.py \
    --run sandbox-slates-v1 --category i-03 \
    --dst projects/01.01-sandbox-in-the-shell/assets/plates

Defaults: source ~/ComfyUI-Shared/output, width 768, JPEG quality 85.
"""

import argparse
from pathlib import Path

from PIL import Image

p = argparse.ArgumentParser(description="collect ComfyUI plates into the repo")
p.add_argument("--run", default="sandbox-slates-v1")
p.add_argument("--category", default=None, help="e.g. i-03 (lowercase path segment)")
p.add_argument("--src", default=str(Path.home() / "ComfyUI-Shared/output"))
p.add_argument("--dst", required=True)
p.add_argument("--width", type=int, default=768)
p.add_argument("--quality", type=int, default=85)
a = p.parse_args()

root = Path(a.src) / a.run
files = sorted(root.rglob("*.png"))
if a.category:
    files = [f for f in files if f"/{a.category}/" in str(f)]
if not files:
    raise SystemExit(f"no plates found under {root}" + (f" for {a.category}" if a.category else ""))

made = 0
for f in files:
    rel = f.relative_to(root).with_suffix(".jpg")
    dst = Path(a.dst) / a.run / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    im = Image.open(f).convert("RGB")
    if im.width > a.width:
        im = im.resize((a.width, round(im.height * a.width / im.width)), Image.LANCZOS)
    im.save(dst, "JPEG", quality=a.quality, optimize=True)
    made += 1
    print("->", dst)

print(f"collected {made} plates")
