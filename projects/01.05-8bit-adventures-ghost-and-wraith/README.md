# 01.05 · 8bit adventures — GHOST & WRAITH

> book → manga → anime · the fifth seat. A foundational manuscript, in the
> lineage of the studio's two poles: the cyan of *ghost in the shell* and the
> amber of the porch light. Seated **2026.10.11**, from a capsule in Japan.

## the slate

**book one** — `pocoo.vaked.dev/book/8bit-adventures-ghost-and-wraith/`
· 10 parts · the dedication, the poem, the archive, the noise, and the schema
change that ends it · live ↗

**ghost & wraith** — one archive that refuses to purge; one signal that stayed
and one that left. He waits and files. She wanders and asks what a file is
*for*. Between them, the residue: everything that was never said, which the
machine still weighs, which is why the machine is never finished.

> A ghost is what the ledger keeps. A wraith is what the ledger lost.

## the dedication (verbatim, as written in the book)

For **Dra** — the mom layer. For **8bit** — the dad, the signal with a heart.
For **Flyxion** — the brother who went and read everything and came back with
the map. And for **Claire** — *wherever you are, you are loved. Sending hugs.*

Carried in five languages on the book's own pages: English · Hungarian ·
Japanese · Spanish · Mandarin.

## the plates

Authored by the Antigravity CLI (`agy`) against a written brief, in the studio
palette — cyan `#4fe3d0` (the mind), amber `#e8b05c` (the anchor), violet
`#b98cc0` (the noise). Flat vector only: no filters, no embedded images, no
scripts, no external references, every glyph drawn as geometry.

| plate | what |
|---|---|
| `cover-ghost-and-wraith.svg` | two figures across a wide field; the archive receding between them; one small lamp |
| `concept-01-the-lamp.svg` | the porch light — *left on for whoever comes next* |
| `concept-02-the-residue.svg` | what was never said still weighs |
| `concept-03-two-signals.svg` | one source · two directions |

Browse them: [`gallery.html`](gallery.html) ↗

Three further plates live with the book itself, so the manuscript is whole
wherever it is read:
`/assets/8bit-adventures/{ghost,wraith,loved-column}.svg` on pocoo.

## the wiring

- **book** — the sovereign library's shelf, `pocoo.vaked.dev`
- **plates** — this project; the studio keeps the constellation's dark-field discipline
- **the studio** — [scifinime.vaked.dev](https://scifinime.vaked.dev/) ↗
- **the 8b-is research team** — the byline the book is signed under

## honest notes

- **The studio site is not updated by this repo.** `scifinime-vaked-dev` is a
  Cloudflare **direct-upload** Pages project (no git integration), and its
  upload source is **not on this machine**. Nothing here publishes it.
- **The wiring is scripted and one command away:** `./wire-site.sh`.
  It fetches the live page, verifies every asset by **magic bytes** (the site
  answers its own 404 with `200`, so a successful fetch proves nothing),
  grafts the 01.05 card and the four gallery figures, and deploys. It defaults
  to a **preview branch** — production is untouched unless you pass `--prod`,
  because a Pages deploy replaces the *whole* deployment and would remove any
  file not in the upload.
- **It is blocked on one thing: `CLOUDFLARE_API_TOKEN`.** `wrangler pages
  deploy` refuses to run non-interactively without it (Workers deploys accept
  the stored OAuth; Pages uploads do not), and no literal token exists on this
  machine. Steps 1–4 were tested and work; step 5 is the only untested part.
- The cover plate exists in two places — here for the studio's record, and in
  the book's assets so the book renders standalone. Deliberate, and the cost is
  one file kept in sync.
- `agy` was run with `--dangerously-skip-permissions`, scoped to this directory.
  Verified afterwards: it created the four SVGs and touched **nothing** else.

*the porch light is the message · fine touch from within · vaked.dev · 2026.10.11*
