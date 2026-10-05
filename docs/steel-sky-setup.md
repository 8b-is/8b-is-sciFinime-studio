# steel-sky — Peter-compatible local setup (M1)

Step-by-step for running [standardgalactic/steel-sky](https://github.com/standardgalactic/steel-sky)
on this machine. Everything below is verified against the upstream README
(read 2026-10-04) and this machine's toolchain. Peter-compatible means:
**`uv` for every Python invocation**, `gh` for cloning, no bare `pip`, no sudo.

## what steel-sky is (the three things)

1. **The catalogue** — 440 screenplay projects in 22 cycles of 20.
2. **Pilot packages** — per project: treatment, scene outline, screenplay,
   visual bible (the studio's spine — see `docs/pipeline.md`).
3. **The image pipeline** — a local ComfyUI service driven by JSON manifests
   (`generate_collection.py`), used to produce visual-bible art.

## requirements (upstream)

- Docker with Compose v2.
- **NVIDIA GPU** + NVIDIA Container Toolkit for the `comfy` profile.
  Without one, use `comfy-cpu` — works, but much slower.
- Python 3.8+ on the host (the runner is stdlib-only;
  `tools/make_thumbs.py` needs `pillow`).
- ~10 GB free disk for models + images.

## the M1 reality check (read this first)

This Mac has no NVIDIA GPU, so the stock `comfy` profile cannot run here.
Two honest paths:

- **Path A — official CPU container** (`comfy-cpu`): zero decision-making,
  slow (minutes per image), fine for validating the pipeline once.
- **Path B — M1 native ComfyUI + the runner's `--url`**: the steel-sky
  runner only talks HTTP to a ComfyUI endpoint (`--url`, default
  `http://127.0.0.1:7860`). Run ComfyUI natively on Metal (MPS) — its own
  install docs — and point the runner at it. This is the recommended path on
  the M1; images keep the same manifest flow.

Text-side near-field is already live locally: **osaurus** on
`http://127.0.0.1:1337` (see §6).

## 0 · prerequisites

```bash
xcode-select -p          # or: ensure Command Line Tools present
docker compose version   # Compose v2 expected
uv --version             # required (the workspace rule)
gh --version
df -h . | tail -1        # want ~10 GB free
```

## 1 · clone

```bash
cd ~/workspace/peterlodri-sec
gh repo clone standardgalactic/steel-sky
cd steel-sky
git branch --show-current   # archdaemon
```

## 2 · get the model files (first time only)

```bash
docker compose --profile download up --build
```

Downloads the Stable Diffusion 1.5 checkpoint (`v1-5-pruned-emaonly.ckpt`)
into `data/models/`.

## 3 · start the image service

**Path A (CPU container):**

```bash
docker compose --profile comfy-cpu up --build
# ComfyUI on http://localhost:7860
```

**Path B (M1 native ComfyUI)** — start your Metal ComfyUI (default
`http://127.0.0.1:8188`), then probe it:

```bash
node -e "fetch('http://127.0.0.1:8188/system_stats').then(r=>r.json()).then(j=>console.log(j.system?.comfyui_version || 'up'))"
```

Probe the container the same way if you want proof:
`node -e "fetch('http://127.0.0.1:7860/system_stats').then(r=>r.json()).then(j=>console.log(j.system?.comfyui_version || 'up'))"`

## 4 · dry-run a manifest

```bash
uv run python generate_collection.py manifests/slate-samples-v4.json --dry-run
```

Expect: the job count + total images first, then each job's full prompt and
negative prompt. No generation.

## 5 · generate

```bash
# one project only (repeat the flag for several)
uv run python generate_collection.py manifests/slate-samples-v4.json --category 01.01

# on Path B, add the URL of your native ComfyUI:
uv run python generate_collection.py manifests/slate-samples-v4.json --category 01.01 --url http://127.0.0.1:8188
```

Images land in `output/comfy/<run-name>/<category>/<item>/`. Progress is
saved in `<manifest-name>.progress.json`; a re-run skips finished jobs.
Interrupted runs stop instead of risking duplicates — check the ComfyUI
queue, then add `--retry-incomplete` to resubmit (may duplicate images).

## 6 · thumbs + local view

```bash
uv run --with pillow tools/make_thumbs.py output/comfy --dst thumbs --size 512 --quality 80
uv run python -m http.server
# open http://localhost:8000
```

Commit `thumbs/`, not `output/`.

## 7 · osaurus (the M1 near-field wire) — verified live

```bash
node -e "fetch('http://127.0.0.1:1337/v1/models').then(r=>r.json()).then(j=>console.log(j.data.map(m=>m.id).join(', ')))"
# foundation, gemma-4-e2b-it-8bit

node -e "fetch('http://127.0.0.1:1337/v1/chat/completions',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({model:'gemma-4-e2b-it-8bit',messages:[{role:'user',content:'Reply with exactly: OK'}],max_tokens:6})}).then(r=>r.json()).then(j=>console.log(j.choices[0].message.content))"
# OK
```

Use it for prompt drafting, treatment passes, and image-description batches
(`image_descriptions.json`) — kept under the studio's 10% local-compute cap.

## 8 · optional: the Arch tooling container

From the upstream README — add `services/arch/compose-snippet.yml` to
`docker-compose.yml`, start ComfyUI, then:

```bash
docker compose --profile arch up --build -d
docker compose exec arch bash
# project at /work; COMFY_URL set inside
uv run python generate_collection.py manifests/my-run.json --url "$COMFY_URL"
```

## 9 · where it plugs into the studio

- New project → copy the pilot order into
  `projects/<slot>/`: `treatment.md`, `scene-outline.md`, `screenplay.md`,
  `visual-bible.md`.
- Visual-bible plates → write a manifest (`manifests/sandbox-slates-v1.json`
  style — copy `slate-samples-v4.json`, change `name`), run it, pick, commit
  `thumbs/`.
- Finished book → the sovereign library lane (`pocoo.vaked.dev/book/<slug>/`).

## gotchas (carried from upstream + this machine)

- No NVIDIA on the M1 → `comfy` profile is out; use `comfy-cpu` or native
  Metal ComfyUI (Path B).
- The runner default URL is `:7860`; native ComfyUI usually listens on
  `:8188` — always pass `--url` on Path B.
- Batch 4 at 512×512 fits modest GPUs; drop `defaults.batch` to 1 if memory
  complains.
- Committing `output/` bloats the repo — only `thumbs/`.

## 10 · the first live plate run (2026-10-04) — halted for machine safety

The studio's plate runner (`tools/zimage_plate.py`) drove the local Comfy
Desktop (Z-Image Turbo, `res_multistep`, 8 steps, 1024²) end-to-end: the
job queued, the graph validated, the sampler engaged. Mid-run it was
interrupted — deliberately — because the numbers did not fit:

| | |
|---|---|
| models | `z_image_turbo_bf16` 11 G + `qwen_3_4b` 7.5 G + `ae` 0.3 G ≈ **18.8 G** |
| machine | M1 with **18 G unified memory**; ~2.3 G free under load |
| swap | reached **24+ G used of 24.5 G** during the run |
| disk | **6.9 G free** (so no counter-download of SD1.5 without cleanup) |

The job was interrupted and models unloaded (`/interrupt` + `/free`), the
queue returned to zero. No plates were produced; nothing was lost.

**To light the plate lane (pick one):**

1. **Quantized Z-Image** — an fp8 or GGUF Q4–Q8 build (~4–8 G) into
   `~/ComfyUI-Shared/models/diffusion_models/`; point the runner at an
   updated workflow with the new `unet_name`. Fits the M1 with room.
2. **SD1.5 lane** (steel-sky's stock model) — ~4 G download + cpu profile;
   free disk first (currently 6.9 G).
3. **Free-memory first** — quit heavy apps and re-run; borderline for a
   single 512² plate.
4. **Remote render** — run the same manifest on a GPU host; outputs are
   portable.

Until then: manifest dry-run verified (13 jobs / 52 images), the runner is
tested, the graphs audited. The lane is wired; it is waiting on memory,
not on code.

**Resolved the same day (2026-10-04, evening):** the SD1.5 lane was lit —
checkpoint downloaded from steel-sky's own `links.txt` and verified
(`sha256 cc6cb271…`), a headless ComfyUI backend started on `:8188`
(`ComfyUI/.venv/bin/python3 -s ComfyUI/main.py --extra-model-paths-config …`),
and `sandbox-slates-v1` category `I.03` produced **12 plates** (`the-house`,
`the-creek`, `porch-lamp` ×4) — collected into the project's `assets/plates/`
with `tools/collect_plates.py`.

**The second lighting (2026-10-05) — the slate finished.** The recipe, seated
so any lap can repeat it:

```bash
# 1. paths (once, seated at ~/ComfyUI-Shared/extra_model_paths.yaml)
#    base_path: /Users/lodripeter/ComfyUI-Shared/models  (+ the type map)
# 2. the server (background; Comfy Desktop may idle without serving — go headless)
cd /Users/lodripeter/ComfyUI-Installs/ComfyUI/ComfyUI && \
  .venv/bin/python main.py --enable-manager --port 8188 \
  --input-directory  /Users/lodripeter/ComfyUI-Shared/input \
  --output-directory /Users/lodripeter/ComfyUI-Shared/output \
  --extra-model-paths-config /Users/lodripeter/ComfyUI-Shared/extra_model_paths.yaml
# 3. the pass (steel-sky dir; same workflow.json + url keep finished jobs skipped)
uv run python generate_collection.py manifests/sandbox-slates-v1.json \
  --url http://127.0.0.1:8188 --category I.01 --category I.02   # then I.04, I.05
# 4. collect + stop the server when done (the lane rests)
```

That lit `I.01`, `I.02`, `I.04`, `I.05` (40 more plates) across two laps and
closed the manifest's promise: **13 jobs / 52 images, all seated** in-repo,
twelve picked into the v2 grid (`assets/plates/sandbox-slates-v1/picks/`).
One item held for regeneration (`wave-interference`). The lane is wired; it
now rests.

*fine touch from within · 0 + 1*
