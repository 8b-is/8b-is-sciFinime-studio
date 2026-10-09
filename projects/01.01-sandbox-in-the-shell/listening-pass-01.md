# listening pass 01 — the temp stems, with ears

*lap 33 · seated 2026-10-07 · the animatic's first audio, measured and heard*

The four temps from lap 32 were synthesized placeholders; the note left
with them said **ears pending**. This pass gives them the ears. Every
claim below is measured ([`tools/listen_stems.py`](../../tools/listen_stems.py)
plus ffmpeg `ebur128`), then read the way a person would read it.
Waveforms, one stripe per stem, drawn from the actual samples:
[`assets/sound/animatic-01-temp/waveforms.png`](assets/sound/animatic-01-temp/waveforms.png).

The generator's intent (lap 32): `four-four-122` — a deep-house loop that
never resolves (8 bars); `creek` — the one clean sound; `whine` — a pure dry
harmonic, mixed-too-dry on purpose; `breath-strip` — in · hold · out, the
act-three metronome.

## the measurements

| stem | dur | loudness | shape | the one number that matters |
|---|---|---|---|---|
| four-four-122 | 15.75 s | I −17.7 LUFS · LRA 0.4 LU · peak −0.8 dBFS | 32 onsets · med 490 ms · 0 silence | kick fundamental **55.3 Hz** (design: 55) |
| creek | 20.00 s | I −27.7 LUFS · LRA 5.5 LU · peak −11.2 dBFS | 0 silence · crest 16 dB | autocorrelation r 0.28 — no tonal centre: weather, not a note |
| whine | 12.00 s | I −13.8 LUFS · **LRA 0.0 LU** · peak −12.2 dBFS | 0 onsets · crest 3.3 dB | est 1575 Hz (lag-quantized; design 1568 ±3 drift) · tail **−2.9 dB** |
| breath-strip | 9.00 s | I −27.0 LUFS · LRA 5.5 LU · peak −12.7 dBFS | 2 silences · longest 0.40 s | in^1.6 · hold ≈ −43 dBFS · out^1.4 |

## what the ears heard

**four-four-122 — rhythmically true, dynamically dead.** The machine keeps
perfect time: 32 onsets at 122.4/min, the kick verifying at 55.3 Hz, edges
loop-clean. But LRA 0.4 LU means it never breathes; a real deep-house loop
pushes and pulls over its eight bars. It also runs hot (−0.8 dBFS peak):
nothing clips, but the ceiling leaves the mix no headroom. *Verdict: keep
as the timing bed; replace with a licensed loop before anything ships —
as lap 32 already ruled: not arithmetic.*

**creek — the point stands: this must become ONE clean field recording.**
The synthesis is honest (continuous, 0 silence, plops 1.4–3.2 s apart by
design) but autocorrelation finds no identity in it — and it is exactly
right that it has none. A creek is a place; you record places. *Verdict:
record it — 60 s minimum, one take, one place; protect the take; it is the
one sound the episode must not fake.*

**whine — the driest thing in the room, exactly as ordered.** LRA 0.0 LU: a
flat line. Tail −2.9 dB vs body: it stops when it stops — no room, no air,
no apology. Measured 1575 Hz (the analyzer's lag resolution at 22.05 kHz;
the source is 1568.0 with the ±3 Hz drift — the uncomfortably-alive wobble —
so the design frequency is intact behind the rounding). *Verdict: keep the
stem dry; if wetness is ever wanted, it gets added in the mix — the stem
stays a blade.*

**breath-strip — the metronome keeps time.** The hold sits at ≈ −43 dBFS:
almost nothing, and the meter still refuses to call it silence — correct.
Two true silences (0.40 s at the head of the inhale and its mirror before
the close). The in^1.6 / out^1.4 asymmetry reads as a body, not a ramp —
visible in the waveform as the slow head and the quicker tail. *Verdict:
the timing skeleton for act three; re-record a human later without touching
the geometry.*

## before anything ships

1. creek → ONE clean field recording (≥ 60 s, one take)
2. four-four → licensed loop (the temps keep the edit only); ceiling TP ≤ −1.0 dB
3. whine → stays 1568 ± 3 Hz drift, stays dry
4. breath → human re-record, keep in^1.6 · hold · out^1.4
5. mix heads: episode LRA ≥ 4 LU — the temps are flatter than the story

## the wire

- generator: [`tools/temp_stems.py`](../../tools/temp_stems.py) (lap 32)
- ears: [`tools/listen_stems.py`](../../tools/listen_stems.py) (this lap)
- seating in the animatic: [`animatic-01-the-dissonant-frequencies.md`](animatic-01-the-dissonant-frequencies.md) § temp sound
- stripes: [`assets/sound/animatic-01-temp/waveforms.png`](assets/sound/animatic-01-temp/waveforms.png)

*fine touch from within · the ears verify last · 0 + 1*
