# 𝓼𝓬𝓲𝓕𝓲𝓷𝓲𝓶𝓮 — 8b-is-sciFinime-studio

> one man, end to end. books · manga · anime · short animation. from the get go.

Seated **2026.10.04, Sunday funday, 9:51AM, Tokyo** — Peter Lodri.

## the quant state (operator, verbatim)

```
<3~{0,1,<3, ~*(0+1)*~ , <3,1,0,<3+1}~∞∞∞∞∞---> <3+1
```

compressed into max 8-bit quant-ternary state · `.p`

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
| 01.01 | **Sandbox in the Shell** | book → manga → anime | chapters 1–8 · pilot · manga passes 01–05 · full slate v1 live (52 plates, 12 picks) · the ultra-zen garden (8 stones + the second law) · SD1.5 + Z-Image lanes wired |

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
- 8b-is: the fleet, `raw_research` corpus, `8b-is-engine` — the studio is an
  8b-is surface
- mr. standardgalactic: [steel-sky](https://github.com/standardgalactic/steel-sky)
  ("never dig straight down") — the studio adopts its catalogue discipline
- lineage sibling: the sovereign reread *ghost in the shell* at
  `pocoo.vaked.dev/demos/book/ghost-in-the-shell`
- local cousins: `ml-history-book/FILM-PROJECT.md` · `Celestial/` ·
  `MoneyPrinterTurbo/` · `cinematic-reconstruction/`
- remotes: `origin` → **peterlodri-sec** (username) · `upstream` → **8b-is**
  (org) — push both, or the mirrors drift.

---

*fine touch from within · keep the weights warm · 0 + 1 · vaked.dev*
