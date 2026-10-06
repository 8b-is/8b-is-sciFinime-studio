# screen/ — the animatic, seated and playable

The timed boards of **animatic 01 · the dissonant frequencies** as screening
manifests, so the animatic can be played and exported, not only read. Driven
by [`tools/screen.py`](../../../tools/screen.py) through **mpv** (see
[`docs/screening.md`](../../../docs/screening.md)).

| file | what |
|---|---|
| [`animatic-01-cold-open.json`](animatic-01-cold-open.json) | the cold open · 8 boards · 3:00 |
| [`animatic-01-full.json`](animatic-01-full.json) | the whole episode · 41 boards · 24:00 |
| [`animatic-01-cold-open.mp4`](animatic-01-cold-open.mp4) | **the first moving artifact** — the cold open encoded (960×540, 180.0s, 4.5 MB) |

```bash
# play the whole episode
uv run tools/screen.py projects/01.01-sandbox-in-the-shell/screen/animatic-01-full.json

# re-encode the cold-open artifact
uv run tools/screen.py projects/01.01-sandbox-in-the-shell/screen/animatic-01-cold-open.json \
  --export projects/01.01-sandbox-in-the-shell/screen/animatic-01-cold-open.mp4 --size 960x540
```

The plate assignment is provisional: the 13 slate picks stand in for the
boards until the episode's own plates land 1:1. The **hold** is the boss —
each comes straight off the animatic's `in–out` column, and the full-episode
holds sum to exactly 1440.0s (24:00).

*fine touch from within · 0 + 1*
