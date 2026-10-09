# the pipeline — one man, end to end

The studio's assembly line, from a paste of an idea to a short animation —
each stage produces the artifact the next stage stands on. No stage may skip
its readme.

```
idea
 └─ bible/          the concept made load-bearing (characters, beats, themes, lineage)
     └─ book/       prose chapters (the literary layer; sovereign library eligible)
         └─ manga/  sequence + panel language (scene outline → storyboard → pages)
             └─ animatic/   timed boards with temp sound (the first moving artifact)
                 └─ short animation/   final motion (steel-sky visual bible → shots)
```

The animatic stage is played, not just written: **the ears**
([`tools/listen_stems.py`](../tools/listen_stems.py)) measure the temp stems
and **the screen** ([`tools/screen.py`](../tools/screen.py)) seats the timed
boards through **mpv** — one plate held for one timecode. See
[`screening.md`](screening.md).

## the Steel Sky spine (per project)

Adopted from [standardgalactic/steel-sky](https://github.com/standardgalactic/steel-sky),
whose pilot packages develop every project in the same order:

1. **treatment** — the story as one breath.
2. **scene outline** — the scenes, titled and ordered.
3. **screenplay** — the written film.
4. **visual bible** — the look, the palette, the motifs, the asset notes.

Then the image pipeline: JSON manifests → the ComfyUI runner (`generate_collection.py`)
→ picks — the machinery that turns a visual bible into candidate frames.

## the book layer (8b-is-native)

Books keep the sovereign-convention: a `book/` directory per project with a
`manuscript` as source of truth and an optional entheai `--fanout` scaffold;
finished books graduate to the sovereign library (`pocoo.vaked.dev/demos/book`).

## the local stack

| stage | tool |
|---|---|
| text near-field (prompts, treatments, passes) | osaurus M1 · `http://127.0.0.1:1337` |
| images (concept frames, visual bible plates) | ComfyUI (local, Metal or container) via steel-sky manifests |
| books | pocoo `book/<slug>/` convention + fan-out |
| animatic playback (boards + temp stems) | **mpv** via [`tools/screen.py`](../tools/screen.py) — [screening.md](screening.md) |
| animatic export (boards → mp4) | **ffmpeg** via `tools/screen.py --export` — [screening.md](screening.md) |
| publishing | the constellation (pocoo · art · music) |

## the standing rules

- **ULTRA-CREATE** every new thing ([definition](ultra-create.md)).
- ULTRABACKYARDLOOP at SOTA, **min: 1024 laps**.
- Local compute ≤ 10%.
- Every stage ends with: verified, committed, pushed, readme'd.

*fine touch from within · 0 + 1*
