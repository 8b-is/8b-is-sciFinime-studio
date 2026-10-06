# the screen — playing the boards through mpv

The animatic stage needs two organs: **the ears** and **the screen**.

- **the ears** — [`tools/listen_stems.py`](../tools/listen_stems.py). Measures
  the sound stems so the notes have numbers (levels, silence, onsets, tone).
- **the screen** — [`tools/screen.py`](../tools/screen.py). Seats the timed
  boards so the picture has numbers too: one plate, held for one timecode,
  over the temp sound bed.

The player is **[mpv](https://github.com/mpv-player/mpv)** — the sovereign
native media player. The studio does not reimplement a video path; it drives
mpv over the CLI, the same way it drives steel-sky over `--url` and the M1
near-field over `http://127.0.0.1:1337`.

```
boards (timed) ──► screen.py ──► ffmpeg concat (per-plate timecodes) ──► mpv ──► the eye
                                    ▲
   stems (measured) ──► listen_stems.py ──► the ear
```

## why mpv

- **one binary, every format** — mpv carries its own FFmpeg; a plate set, a
  ProRes animatic export, a PNG sequence, a WAV bed — all the same command.
- **per-frame exactness** — with the `concat` demuxer, mpv honours each
  plate's duration to the millisecond. The board's timecode is the boss:
  `duration 26.000` means twenty-six seconds, not "about".
- **headless** — `--vo=image` renders frames to PNG with no display. The
  screen can be verified in CI, on a server, or on a laptop lid-closed.
- **scriptable** — mpv's IPC and CLI are stable; the studio treats it as
  infrastructure, not a GUI to click.

## the GPL line

mpv is **GPLv2+**; the studio is MIT. They stay separate processes: `screen.py`
`exec`s mpv, it never imports or links it. Shipping mpv *with* the studio, or
linking `libmpv`, would pull the GPL across the boundary — so the studio
**depends on** mpv being present, it does not **bundle** it. This is the same
call the constellation makes for steel-sky, ComfyUI, and ffmpeg.

## the drop-in path

`screen.py` finds mpv in this order: `--mpv`, `$MPV`, `PATH`, then the
standard macOS bundle `/Applications/mpv.app/Contents/MacOS/mpv`, Homebrew
(`/opt/homebrew/bin/mpv`, `/usr/local/bin/mpv`), `/usr/bin/mpv`, and
`~/.local/bin/mpv`. If none exist it prints the install line and exits `127`.

| platform | install |
|---|---|
| macOS | `brew install mpv` — or drop `mpv.app` into `/Applications` |
| Debian/Ubuntu | `apt install mpv` |
| Fedora | `dnf install mpv` |
| Arch | `pacman -S mpv` |

This machine (verified 2026-10-07): `/Applications/mpv.app/Contents/MacOS/mpv`
· `mpv v0.41.0-dev-geb0ee1031` · FFmpeg `9.0.2`.

## the grammar

A screening is a JSON manifest under the project's `screen/` directory. Paths
are relative to the studio root.

```json
{
  "title": "animatic 01 · the dissonant frequencies — cold open (0:00–3:00)",
  "audio": ["projects/01.01-sandbox-in-the-shell/assets/sound/animatic-01-temp/four-four-122.wav"],
  "boards": [
    {
      "board": "1.1",
      "hold": 26,
      "plate": "projects/01.01-sandbox-in-the-shell/assets/plates/sandbox-slates-v1/picks/shinjuku-rain.jpg",
      "action": "Rain-slicked crossing, neon smeared, cooling towers steaming. Slow push in."
    }
  ]
}
```

- `hold` — seconds the plate is held. Lift it straight off the animatic's
  `in–out` column; the timecode is the boss.
- `plate` — the image. A provisional board can point at a slate pick; when
  the episode's real plate lands, it replaces the pick 1:1 — the timecode
  does not move.
- `audio` — the temp bed (one or more files). Defaults to silence if absent.
- `board` / `action` — provenance, carried into the plan print.

## running it

```bash
# dry-run: resolve mpv, build the board list, print the plan (no window)
uv run tools/screen.py --dry-run

# screen it (a window opens; space pauses, q quits)
uv run tools/screen.py

# headless proof — render the boards to PNGs, no display needed
uv run tools/screen.py --render /tmp/screen-out --frames 8

# any directory of plates, a fixed hold, no manifest
uv run tools/screen.py --dir path/to/plates --hold 4

# the whole episode (41 boards, 24:00)
uv run tools/screen.py projects/01.01-sandbox-in-the-shell/screen/animatic-01-full.json

# keep the board list next to the work (reproducible artifact)
uv run tools/screen.py --edl screen/animatic-01-cold-open.ffconcat
```

## the verified pass

The cold open screens clean. Verified 2026-10-07:

```
screen: animatic 01 · the dissonant frequencies — cold open (0:00–3:00)
player: mpv v0.41.0-dev-geb0ee1031
        /Applications/mpv.app/Contents/MacOS/mpv
boards: 8 · runtime 180.0s (3.00 min)
  audio four-four-122.wav
    26.0s    [1.1]  shinjuku-rain.jpg
    26.0s    [1.1]  the-window.jpg
    24.0s    [1.2]  the-gate.jpg
    24.0s    [1.3]  porch-lamp.jpg
    24.0s    [1.4]  the-turn.jpg
    24.0s    [1.5]  the-tank-room.jpg
    24.0s    [2.1]  the-descent.jpg
     8.0s  [title]  wave-interference.jpg
```

`--render` wrote 8 frames (one per board, 512×512 PNG) — the screen works
with no display. `tests/test_screen.py` (15 cases) pins the player
resolution, manifest parsing, the concat grammar, and the headless command.

The **full episode** screens too: `screen/animatic-01-full.json` carries all
41 boards straight off the animatic's in–out column, and the holds reconcile
exactly —

```
boards: 41 · runtime 1440.0s (24.00 min)
```

— matching the animatic's stated 24:00 runtime to the second. `--render`
wrote 42 frames in ~4.4s, headless. Two screenings are seated: the cold open
(`animatic-01-cold-open.json`, 8 boards, 3:00) and the whole episode
(`animatic-01-full.json`, 41 boards, 24:00).

The ears still verify last: **a branch may be ranked; only a verified branch
may be bound.**

---

*fine touch from within · keep the weights warm · 0 + 1 · vaked.dev*
