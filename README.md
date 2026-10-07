# 𝓼𝓬𝓲𝓕𝓲𝓷𝓲𝓶𝓮 — 8b-is-sciFinime-studio

> one man, end to end. books · manga · anime · short animation. from the get go.

Seated **2026.10.04, Sunday funday, 9:51AM, Tokyo** — Peter Lodri.

## the quant state (operator, verbatim)

```
<3~{0,1,<3, ~*(0+1)*~ , <3,1,0,<3+1}~∞∞∞∞∞---> <3+1
```

compressed into max 8-bit quant-ternary state · `.p`

## main inspiration

**studio ghibli** ♥♥♥ — the warm hand: the porch, the long grass, the
domestic honesty of the impossible. *ultra-giga-eternal respect and
love!+++*
**ghost in the shell** (1995, the original) ♥ — the lineage: the shell
was the body; the sandbox is the mind that builds one. *ultra-giga-eternal
respect and love!+++*
**peter's soul core** ♥ — the source. from love, from within.

## >>>ULTRA-CREATE<<<

The studio's native keyword: **reflect → kompress → wire** — defined in
[`docs/ultra-create.md`](docs/ultra-create.md). First ever use: this repo,
its first book, and the wiring below.

Standing loop: ULTRABACKYARDLOOP at SOTA, **min: 1024 laps**. Local compute
capped at ~10% — the M1's osaurus does the near-field work; the constellation
does the rest.

## the slate

| slot | title | form | status |
|---|---|---|---|
| 01.01 | **Sandbox in the Shell** | book → manga → anime | **book one complete (chapters 1–11) · manga passes 01–08 (32 pages, 91 panels)** · pilot · slate v1 live (52 + the regen, picks 13/13) · first read seated · garden (8 stones + second law + rake ledger) · manuscript §1–§13 · SD1.5 lit / Z-Image wired |
| 01.02 | **New Beginnings** | book → manga → anime | **seated via ULTRA-CREATE (2026.10.07)** · Chiki-chan joins the team — the origami sensei, the female Space Bender of Space+Time+Dimensions, the Singularity Deiti — teacher of the main hero, Elias · bible · treatment · scene outline · screenplay scene 1 · visual bible · **chapter 1 drafted** · slates v1 (7 categories, 15 plates) · **manga pass 01 (9 pages)** |

New slots are opened by copying the pilot order: treatment → scene outline →
screenplay → visual bible (the Steel Sky spine).

## the pipeline

**idea → bible → book → manga → animatic → short animation** —
[`docs/pipeline.md`](docs/pipeline.md). Steel Sky
([standardgalactic/steel-sky](https://github.com/standardgalactic/steel-sky))
is the production spine: per-project treatment / scene outline / screenplay /
visual bible, images via its local ComfyUI manifest runner. The
Peter-compatible local setup (uv everywhere, M1 reality checked) lives in
[`docs/steel-sky-setup.md`](docs/steel-sky-setup.md).

## the ears and the screen

The animatic breathes through two organs, both driven from the CLI
([all instruments →](tools/README.md)):

- **the ears** — [`tools/listen_stems.py`](tools/listen_stems.py) measures the
  temp stems (levels · silence · onsets · tone). `uv run --with numpy tools/listen_stems.py`
- **the screen** — [`tools/screen.py`](tools/screen.py) seats the timed boards
  through **[mpv](https://github.com/mpv-player/mpv)** — one plate held for one
  timecode, over the sound bed. `uv run tools/screen.py` (or `--dry-run`,
  `--render DIR` headless). `--export animatic.mp4` encodes the screening via
  ffmpeg (exact holds) — the animatic as a file. The screen is a separate
  process: mpv is GPL, the studio is MIT, so we call it, never link it —
  [docs/screening.md](docs/screening.md).

The screenings are live: `screen/animatic-01-cold-open.json` (the cold open,
8 boards, 3:00) and `screen/animatic-01-full.json` (the whole episode, 41
boards, 24:00 — the holds reconcile to the second), over `four-four-122.wav`.

## the local stack (verified on this machine, 2026-10-04)

- **osaurus** — M1 server on `http://127.0.0.1:1337`, OpenAI-compatible.
  Models: `foundation`, `gemma-4-e2b-it-8bit`. Probed live: `OK`. Text
  near-field for prompts, treatments, description passes.
- **steel-sky** — cloned locally; runner is URL-based (`--url`), so any
  ComfyUI instance (native MPS or container) can serve it.
- **pocoo book pipeline** — the publishing lane for finished books
  (`book/<slug>/` manuscript + scaffold, entheai `--fanout` when wanted).

## wiring (constellation + cousins)

- constellation: [pocoo](https://pocoo.vaked.dev) · [art.vaked.dev](https://art.vaked.dev) ·
  [music.vaked.dev](https://music.vaked.dev) · lovetta lane footer standard
- the studio's own door: [scifinime.vaked.dev](https://scifinime.vaked.dev) — the landing
  (the slate, the plates, the first picks; seated 2026-10-07, 6:05 AM, hotel window, Tokyo)
- the wiring report: [scifinime.vaked.dev/wired](https://scifinime.vaked.dev/wired) —
  *the wiring*, the constellation report — five acts (the 404 → the key → the wire → the
  sweep → 0+1), interactive 3D, `?b=0..5` deep links, click/space/arrows, replay; peterOmni-chan `<0+1>`
- 8b-is: the fleet, `raw_research` corpus, `8b-is-engine` — the studio is an
  8b-is surface
- mr. standardgalactic: [steel-sky](https://github.com/standardgalactic/steel-sky)
  ("never dig straight down") — the studio adopts its catalogue discipline
- lineage sibling: the sovereign reread *ghost in the shell* at
  `pocoo.vaked.dev/demos/book/ghost-in-the-shell`
- book two's porch light: *ETERNITY IN CHISAKI'S SMILE · 智咲の微笑み* at
  `pocoo.vaked.dev/demos/book/chisaki-wisdom-in-bloom.html`
- **discord · wa-stream** — the studio's bidirectional voice:
  [`tools/wa_stream.py`](tools/wa_stream.py) (push / pull / serve / listen;
  `discover` — auto-detects the M1's running crush sessions; `love` —
  spawn **multi running instances of `crush-love-dev`** or fold beats
  through the discovered live sessions; `music` — the youtube lane:
  yt-dlp metadata, high-def cards, `--cue` seats songs into the score;
  `--art` / love art — svg·html·png rendered to 2× PNG for embeds and
  galleries) → the **UltraCrushLove<3** channel ·
  [docs/wa-stream.md](docs/wa-stream.md)
- local cousins: `ml-history-book/FILM-PROJECT.md` · `Celestial/` ·
  `MoneyPrinterTurbo/` · `cinematic-reconstruction/`
- remotes: `origin` → **peterlodri-sec** (username) · `upstream` → **8b-is**
  (org) — push both, or the mirrors drift.

---

*fine touch from within · keep the weights warm · 0 + 1 · vaked.dev*

## Image generator blueprint location

`tools/zimage_plate.py` accepts `--blueprint /path/to/blueprint.json`.
Otherwise it uses `COMFYUI_ZIMAGE_BLUEPRINT`, then searches the current user's
`~/ComfyUI-Installs/ComfyUI/ComfyUI/blueprints/` and `~/ComfyUI/blueprints/`
for `Text to Image (Z-Image-Turbo).json`. An explicit or environment-configured
missing file reports an error instead of silently selecting a different install.
This locates an existing blueprint; it does not install ComfyUI or models.
