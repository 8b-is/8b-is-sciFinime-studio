#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# ///
"""zimage_plate.py — generate a plate with Z-Image Turbo on the local ComfyUI.

Reads the ComfyUI Z-Image Turbo blueprint (the subgraph template that ships
with ComfyUI), converts it to an API graph, injects prompt/size/steps/seed,
submits to the local ComfyUI, waits, and prints each saved image path.

Peter-compatible: stdlib only, run it via uv from the studio root:

  uv run tools/zimage_plate.py \
    --prompt "small family house at dusk, one porch lamp burning warm amber ..." \
    --prefix sandbox-slates-v1/porch-lamp --seed 20261004

Notes:
- Z-Image Turbo runs at cfg=1 with a zeroed negative (the blueprint's
  ConditioningZeroOut), so a negative prompt has no effect on this lane.
- Images land in the ComfyUI app's output directory (Comfy Desktop:
  ~/ComfyUI-Shared/output). Copy picks into the project's assets/; the
  platform's own advice stands: commit thumbs, not raw runs.
"""

import argparse
import json
import os
import secrets
import sys
import time
from pathlib import Path
from urllib import error, request

BLUEPRINT_NAME = "Text to Image (Z-Image-Turbo).json"


def resolve_blueprint(explicit=None):
    """Prefer an explicit path, then configuration, then common local installs."""
    configured = explicit or os.environ.get("COMFYUI_ZIMAGE_BLUEPRINT")
    if configured:
        candidate = Path(configured).expanduser()
        if candidate.is_file():
            return candidate
        raise FileNotFoundError(
            f"Blueprint not found: {candidate}. Set --blueprint to an existing "
            "Z-Image Turbo blueprint JSON file."
        )
    home = Path.home()
    candidates = [
        home / "ComfyUI-Installs/ComfyUI/ComfyUI/blueprints" / BLUEPRINT_NAME,
        home / "ComfyUI/blueprints" / BLUEPRINT_NAME,
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(
        "Z-Image Turbo blueprint not found. Pass --blueprint /path/to/"
        f"'{BLUEPRINT_NAME}' or set COMFYUI_ZIMAGE_BLUEPRINT. "
        "Checked: " + ", ".join(str(path) for path in candidates)
    )


WIDGETS = {
    "CLIPLoader": ["clip_name", "type", "device"],
    "VAELoader": ["vae_name"],
    "UNETLoader": ["unet_name", "weight_dtype"],
    "CLIPTextEncode": ["text"],
    "EmptySD3LatentImage": ["width", "height", "batch_size"],
    "ModelSamplingAuraFlow": ["shift"],
    "KSampler": [
        "seed", "control_after_generate", "steps", "cfg",
        "sampler_name", "scheduler", "denoise",
    ],
    "VAEDecode": [],
    "ConditioningZeroOut": [],
}


def api(url, path, payload=None):
    data = None if payload is None else json.dumps(payload).encode()
    req = request.Request(
        url.rstrip("/") + path, data=data,
        headers={"Content-Type": "application/json"},
    )
    try:
        with request.urlopen(req, timeout=60) as r:
            return json.load(r)
    except error.HTTPError as e:
        raise RuntimeError(
            f"HTTP {e.code}: {e.read().decode(errors='replace')[:400]}"
        ) from e


def to_api_graph(sg):
    links = {l["id"]: l for l in sg.get("links", [])}
    node_ids = {str(n["id"]) for n in sg["nodes"]}
    graph = {}
    for n in sg["nodes"]:
        t = n["type"]
        if t not in WIDGETS:
            raise ValueError(f"Unsupported node type in blueprint: {t}")
        inputs = {}
        wv = n.get("widgets_values", [])
        for i, name in enumerate(WIDGETS[t]):
            if name == "control_after_generate":
                continue
            if i < len(wv):
                inputs[name] = wv[i]
        for entry in n.get("inputs", []):
            lid = entry.get("link")
            if lid is None or lid not in links:
                continue
            l = links[lid]
            if str(l["origin_id"]) not in node_ids:
                continue  # subgraph input proxy (-10) — keep the widget default
            inputs[entry.get("name") or entry.get("label")] = [
                str(l["origin_id"]), l["origin_slot"],
            ]
        graph[str(n["id"])] = {"class_type": t, "inputs": inputs}
    return graph


def main():
    p = argparse.ArgumentParser(description="Z-Image Turbo plate generator")
    p.add_argument("--blueprint", help="Blueprint JSON path (overrides COMFYUI_ZIMAGE_BLUEPRINT and local discovery)")
    p.add_argument("--prompt", required=True)
    p.add_argument("--prefix", default="sandbox-plate")
    p.add_argument("--width", type=int)
    p.add_argument("--height", type=int)
    p.add_argument("--steps", type=int, default=8)
    p.add_argument("--seed", type=int, default=None)
    p.add_argument("--url", default="http://127.0.0.1:8188")
    p.add_argument("--timeout", type=float, default=900)
    a = p.parse_args()

    blue = json.loads(resolve_blueprint(a.blueprint).read_text())
    sg = blue["definitions"]["subgraphs"][0]
    graph = to_api_graph(sg)

    graph["27"]["inputs"]["text"] = a.prompt
    if a.width:
        graph["13"]["inputs"]["width"] = a.width
    if a.height:
        graph["13"]["inputs"]["height"] = a.height
    graph["13"]["inputs"]["batch_size"] = 1
    graph["3"]["inputs"]["steps"] = a.steps
    seed = a.seed if a.seed is not None else secrets.randbits(48)
    graph["3"]["inputs"]["seed"] = seed
    graph["save"] = {
        "class_type": "SaveImage",
        "inputs": {"images": ["8", 0], "filename_prefix": a.prefix},
    }

    res = api(a.url, "/prompt", {"prompt": graph})
    if res.get("node_errors"):
        raise RuntimeError(json.dumps(res["node_errors"], indent=2))
    pid = res["prompt_id"]
    print(f"queued {pid} seed={seed}", flush=True)

    deadline = time.monotonic() + a.timeout
    while time.monotonic() < deadline:
        h = api(a.url, f"/history/{pid}")
        if pid in h:
            out = h[pid]
            st = out.get("status", {})
            if st.get("status_str") == "error":
                raise RuntimeError(json.dumps(st, indent=2))
            imgs = [
                i for o in out.get("outputs", {}).values()
                for i in o.get("images", [])
                if i.get("type") == "output"
            ]
            for i in imgs:
                print("saved:", (Path(i.get("subfolder", "")) / i["filename"]))
            if imgs:
                return
            if st.get("completed"):
                raise RuntimeError("completed without saved images")
        time.sleep(2)
    raise TimeoutError("timed out waiting for the job")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError, RuntimeError, TimeoutError) as e:
        print("error:", e, file=sys.stderr)
        sys.exit(1)
