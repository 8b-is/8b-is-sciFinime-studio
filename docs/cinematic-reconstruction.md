# cinematic-reconstruction — the world-state frame

The studio's motion stages (animatic → short animation) need a theory of
*what a frame is*. [`8b-is/cinematic-reconstruction`](https://github.com/8b-is/cinematic-reconstruction)
supplies it: **video is not a sequence of synthesized images; it is a sequence
of camera observations of a persistent, evolving world state.**

Written by **Flyxion** (Independent Researcher, 2026). Source of truth lives in
that repo — `documents/cinematic-reconstruction.tex` (with `.pdf` and `.txt`);
this page is the wiring, not a copy.

## why the studio cares

The pipeline (`idea → bible → book → manga → animatic → short animation`) keeps
one thing invariant at every stage: **the world is persistent; each artifact is
a partial observation of it.** A page is not a picture, it is an observation
from a camera at a time. The framework formalizes exactly that, and it gives the
motion stage the operators the studio currently improvises.

## the mapping (framework ↔ studio)

| cinematic-reconstruction | the studio's stage |
|---|---|
| **World state + frame observation** | the per-project *bible* — the persistent world; the book, the manga page, the animatic plate are observations of it |
| **Admissible reconstruction** | the *picks* — a candidate frame is admissible only if it is consistent with the world, not merely plausible |
| **Heterogeneous algorithm repertoire** | the multi-pass slate (SD1.5 lit · Z-Image wired · the regen) — many independent proposers, not one model |
| **Witnesses and disagreement** | the review verdicts (`screening.md`, `tools/screen.py`) — disagreement is diagnostic, not noise |
| **Structural glitches as evidence** | the QC pass — a broken hand or a wrong shadow localizes *which* operator failed and where |
| **Style as a realization operator** | manga → anime — style *realizes* the same world, it does not regenerate it |
| **Narrative continuation & story state** | book → manga → animatic continuation — `01.01 Sandbox in the Shell`, `01.02 New Beginnings` |
| **Provenance & evidentiary history** | the constellation spine — prove it, don't assert it; SHA-256, receipts |
| **Operator algebra for interactive cinema** | **the ears** (`tools/listen_stems.py`) and **the screen** (`tools/screen.py`) — time as an operator on the plate |

## how it wires

- **Reference, not vendored.** The TeX lives in the framework's repo; the studio
  cites it (below) and links it here. Add `documents/` to the studio only if a
  project needs to build the PDF locally.
- **The motion stage.** When the animatic graduates to shots, the
  *structure-aware rate-distortion* objective and the *structural-invariant*
  checks become the review rubric: degradation is typed, not averaged.
- **The narrative lane.** *Narrative continuation and story state* is the
  formal name for what `docs/pipeline.md` already does between book and manga.

## links

- Repo — <https://github.com/8b-is/cinematic-reconstruction>
- Paper — `documents/cinematic-reconstruction.pdf` (TeX source alongside)
- The studio pipeline — [`pipeline.md`](pipeline.md)
- The screening organ — [`screening.md`](screening.md)

*the pipeline: idea → bible → book → manga → animatic → short animation ·
the world stays; the frame observes · fine touch from within · vaked.dev*
