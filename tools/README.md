# tools/ — the studio's instruments

One tool per organ of the pipeline. Most run as plain scripts
(`uv run tools/<name>.py …`); the two with inline dependencies
(`collect_plates`, `zimage_plate`) carry a PEP 723 header, so `uv run tools/<name>.py`
provisions them on the spot. Every tool is offline-testable; the pytest suite
lives in [`../tests/`](../tests/).

| tool | organ | what it does |
|---|---|---|
| [`listen_stems.py`](listen_stems.py) | **the ears** | measure a WAV stem — levels · silence · onsets · tone → the notes have numbers |
| [`screen.py`](screen.py) | **the screen** | play the timed boards through **mpv**; `--render` headless · `--export` to MP4 via ffmpeg — one plate held for one timecode, over the bed |
| [`temp_stems.py`](temp_stems.py) | the temp sound | synthesize the four animatic stems (four-four · creek · whine · breath-strip) as honest placeholders |
| [`collect_plates.py`](collect_plates.py) | the eye | copy a ComfyUI run's plates into the repo as commit-friendly JPGs (commit picks, not raw runs) |
| [`zimage_plate.py`](zimage_plate.py) | the eye | generate a plate with Z-Image Turbo on the local ComfyUI (blueprint → API graph) |
| [`manuscript_pass.py`](manuscript_pass.py) | the book | convert a prose chapter into the pocoo `book/<slug>/manuscript.html` conventions |
| [`wa_stream.py`](wa_stream.py) | the voice | the bi-directional Discord bridge (push / pull / serve / love) → UltraCrushLove<3 |

The ears and the screen are a pair: the ears measure the bed, the screen seats
the boards — the animatic is *heard* and *watched*, not just read. See
[`../docs/screening.md`](../docs/screening.md) and
[`../docs/wa-stream.md`](../docs/wa-stream.md).

*fine touch from within · keep the weights warm · 0 + 1*
