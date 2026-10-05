# visual bible · Sandbox in the Shell

*The look: a temple built inside a submarine. Bioluminescent weather.
Instrument-light faces. The impossible, rendered as geometry that is
politely, catastrophically wrong.*

## palette

| role | color | where |
|---|---|---|
| ground | trench black-teal `#05131A` | every exterior, the deep layers |
| memory | bioluminescent cyan `#4FE3D0` | the oceans of waves, displays |
| anchor | warm amber `#E8B05C` | the childhood home, the porch lamp, Anya's coffee |
| noise | pure white harmonic `#FFFFFF` | the dissonant frequency — used sparingly, terrifying |
| the Architect | cold violet `#8A7CFF` | firewalls, HUDs he "builds" |
| the Child | rose `#FF7FA3` | glimpses, small warm signals, hand-light |
| the entity | shadow-and-light stipple | never a solid; always +/− interference |

Constellation ties: the art surface's dark-field discipline, but the book
keeps **its own ink** — no crossover logos in-frame.

## the waves (the world's one law)

- All memory is rendered as **wave fields**: interference, moiré, standing
  patterns, echoes.
- Softness is health; hard spikes are pain; a **flat line** is neither —
  it is the absence of the person, used once in the whole book.
- Text/typography: chapter marks are waveform glyphs; UI text never floats —
  it surfaces *in* the water.

## the layers (camera rules)

| layer | rule |
|---|---|
| clinic / real world | wet glass, practical light, handheld when internal |
| layer 1 — the ocean of his mind | wide, slow, bioluminescent; camera floats |
| layer 1 — the home + the creek | amber, still, long lenses; the porch lamp is the sun; the creek runs below the fence — the episode's one clean natural sound |
| layer 2 — the recurring memory | tighter, grainier; the room remembers more than he does |
| the impossible | rule-of-thirds broken on purpose; non-euclidean geometry lit by interference |

## the city (shinjuku)

- The four-four is a character: a deep house pulse that never resolves;
  the city keeps time — towers, traffic, droplets.
- Rain + neon read as signal through fiber; cooling towers as circuits left
  out in weather.
- **The pilot's one visual law:** Shinjuku is a circuit, the mind is an
  ocean, and the porch lamp is the only sun in either.

## the entity

- First read: a **standing wave** that holds a shape the eye keeps almost
  resolving. Light and shadow stippled at the whine's exact frequency.
- Never creature-coded: no eyes, no mouth, no limbs until one reach.
- The reach is the only "body" beat in the episode — one motion, held long.

## asset notes (for the steel-sky pass)

- Manifest: `manifests/sandbox-slates-v1.json` — categories per plate set:
  - `I.01` tank interiors (chapel-machine, wet glass, pumps)
  - `I.02` ocean of waves (bioluminescent weather, wide)
  - `I.03` the childhood home (amber, porch lamp, long lens)
  - `I.04` impossible geometry (non-euclidean, interference-lit)
  - `I.05` the entity (standing-wave figure, stipple, one reach)
- Batch 4 @ 512×512 to start; keep prompts palette-locked to the table above.
- Negative prompts: **avoid literal Ghost in the Shell imagery** — no
  thermoptic-visual humans, no spider-tanks, no 1995 iconography. This
  continuation earns its own frames.
- Reference lanes already in the workspace: `Celestial/` for procedural
  sky/space plates; `art.vaked.dev` for the dark-field finish; `osaurus`
  on `:1337` for prompt drafting and image-description passes.

## plates — the first live run (2026-10-04)

12 plates generated on the SD1.5 lane (`sandbox-slates-v1`, category
`I.03`, seeds from the manifest), collected to
[`assets/plates/sandbox-slates-v1/i-03/`](assets/plates/sandbox-slates-v1/i-03/)
as repo-friendly JPGs (768px, q85; originals stay in ComfyUI's output).

What the three reads gave (viewed, not guessed):

- **the-house** — lavender dusk, one lit porch, a moon over the field; warm
  storybook nostalgia.
- **porch-lamp** — amber lantern close-up against deep blue; the bookmark
  motif, on the first try.
- **the-creek** — a winding creek through clay banks; quiet, painterly.

Register note, honest: SD1.5's aesthetic is *storybook memory*, not 1990s
cel. For the I.03 memory category that register is a gift; the anime
register for the other categories wants the 2026 lane (quantized Z-Image)
or prompt work. Both lanes are wired; this one is lit.

## plates — the second live run: I.01/I.02 (2026-10-05)

24 more plates on the same lane (`sandbox-slates-v1`, categories `I.01` and
`I.02`, batch 4, seeds from the manifest), collected beside the first, 36
plates in-repo.

What the reads gave (viewed, not guessed — six plates across six items):

- **the-tank-room** — a bright teal-and-orange interior with a round pool,
  flat graphic planes. Off the dark-clinic brief; charming as *the tank
  remembered*, not the tank seen. A candidate register for layer-one
  interiors if the picks want warmth over trench.
- **shinjuku-rain** — hard-edged neon street, flat color blocks, pink over
  black; the closest this lane has come to the episode's cel look. A real
  gift for a city plate.
- **monitoring-deck** — a playful flat room with a great round "moon" light;
  the moon motif arriving unasked is the kind of accident picks exist for.
- **adult-ocean** — deep teal water under a heavy sky, soft long waves;
  usable, honest surface calm for the ocean of waves.
- **the-descent** — blue-into-yellow serene sea; a *surface* read. The dark
  pressure descent still wants the other lane or heavier prompting.
- **wave-interference** — pastel gradient bands; off-brief, with a faint
  signature artifact survived the negative prompt. Reserve; regenerate in
  the picks pass if the grid needs it.

Register note, updated: the lane keeps splitting into two gifts — a flat
paper-cut cel (city, rooms) and a soft pastel painter (seas). The dark
bioluminescent register is still the joint work of prompting and the 2026
lane. Picks will choose per item; the palette table stays the referee.

*fine touch from within · 0 + 1*

## the grid v2 — the picks (2026-10-05)

Twelve of thirteen items picked (one held, honestly), seated in
[`assets/plates/sandbox-slates-v1/picks/`](assets/plates/sandbox-slates-v1/picks/)
— one plate per item, the v2 visual bible's working grid. Criteria, in
order: palette lock (the table at the top of this file is the referee),
register (does it read like the book, or like a nice picture next to the
book), motif accuracy (the lamp, the wave, the wrongness).

| item | pick | why |
|---|---|---|
| the-tank-room | variant 1 | bright teal-and-orange planes; *the tank remembered* — warmth over trench, kept for its flat charm |
| shinjuku-rain | variant 2 | hard neon blocks, pink over black — the closest the lane has come to the episode's cel |
| monitoring-deck | variant 1 | the flat room with the round moon light; the accident the picks keep |
| adult-ocean | variant 1 | deep teal under a heavy sky; the ocean's honest surface calm |
| the-descent | variant 1 | serene blue-into-yellow sea; a surface read for the descent, registered as such |
| wave-interference | *held* | pastel bands + a surviving signature artifact; regenerate in the next pass rather than seat it |
| the-house | variant 1 | lavender dusk, one lit porch, a moon over the field (lap-5 read) |
| the-creek | variant 1 | winding water through clay banks; quiet, painterly (lap-5 read) |
| porch-lamp | variant 1 | amber lantern against deep blue; the bookmark motif, first try (lap-5 read) |
| the-turn | variant 1 | folding walls in hatched linework, wrong angles that hold — impossible geometry, finally delivered |
| the-gate | variant 1 | monochrome hatchwork arch; reads like an etching of the book's own gate — the strongest single plate of the slate |
| first-reach | variant 1 | stippled dusk and treeline; not the entity — a porch seen from outside, kept as a gift |
| the-window | variant 1 | glowing arc-pulses over a dark horizon; the closest anything has come to the entity's light |

The held item and any regenerate work are the next plate pass's first
rows. The rake keeps its shape; the sand keeps changing.

*fine touch from within · 0 + 1*
