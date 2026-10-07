# first date — one-shot kickstart (Gemini image gen + local Z-Image)

**scene** · Chi-chan (村田 智咲, the origami sensei) + Omni Peter — their first date.
**the subject is the flow** · origami in the hands; the Tokyo ↔ Haneda loop, back and forth.
**vibe-match** · Billie Eilish — *CHIHIRO (Black Coffee Remix)* — warm-cool, unhurried, in motion.

---

## the one-shot prompt (paste as-is — Gemini / any text-to-image model)

> anime film background art meets a tender character study: washi paper and sumi ink
> over a warm cream field, ink-black linework, one vermilion seal accent, thin veins of
> gold and rose light along every fold — two figures seen from behind on a late train
> running the Tokyo ↔ Haneda loop, a young woman folding a small paper crane in her
> hands and a man beside her watching, the window a wash of soft rose-and-amber
> light-trails left by the back-and-forth, city glow bleeding to airport blue,
> unhurried, cinematic, full bleed drawing that fills the entire image,
> no text, no watermark, no frame

## the local lane (Z-Image Turbo — the studio's own, run via uv)

```bash
uv run tools/zimage_plate.py \
  --prompt "<the one-shot prompt above, kept verbatim>" \
  --prefix new-beginnings-first-date/the-first-date-tokyo-haneda \
  --seed 20261007
```

The `shared_prompt` (style) and `defaults` (batch · seed · negative) live in
`manifests/new-beginnings-slates-v1.json`; the plate is category **II.07**.

## negative (from the manifest defaults)

text, letters, words, watermark, logo, signature, caption, handwriting, photorealistic,
photograph, 3d render, blurry, distorted, extra fingers, deformed hands, picture frame,
frame, mat, border, torn paper, rips, creases crossing over faces, mask with eyes,
wooden puppet, marionette

## plates (II.07)

- `the-first-date-tokyo-haneda` — the two on the late train, the crane in her hands.
- `the-crane-between-two-hands` — the crane passed at the airport railing, runway lights soft.

seed `20261007` · picks land in the studio `assets/` and the gallery
(commit thumbs, not raw runs).

*vibe-match: Billie Eilish — CHIHIRO (Black Coffee Remix) · from love, from within · 0 + 1*
