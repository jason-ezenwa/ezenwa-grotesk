# Ezenwa Grotesk — type specification

## Intent

A contemporary grotesque sans for product user interfaces and brands. Compact
and dense, with closed apertures and a warm, slightly round rhythm. Built to
stay legible at 12–14px, with character at display sizes.

## Lineage

It is built on Archivo (OFL) with Founders Grotesk as a reference. No outlines,
kerning or per-glyph widths are taken from Founders Grotesk.

## Proportions

Values in a 1000-unit em.

| | Value |
|---|---|
| Cap height | 640 |
| x-height | 470 (47% of the em; 0.73 of cap height) |
| Ascender | 640 (flush with cap height) |
| Descender | −170 |
| Overshoot | about 12 |
| Mean lowercase advance (Regular) | about 467 |

Line box: ascent 960 and descent 220, no line gap (hhea and typo alike).

## Weights

| | Light | Regular | Medium | Semibold | Bold |
|---|---|---|---|---|---|
| Lowercase stem | 63 | 85 | 123 | 148 | 166 |
| Capital stem | 65 | 89 | 128 | 156 | 174 |

Each weight has a matching italic.

## Character

- **Apertures:** closed. The tips of C and c nearly meet; the ends of S and s
  curl toward the spine.
- **Curves:** full and slightly round.
- **Terminals:** horizontal or near-horizontal cuts.
- **Corners:** sharp, never rounded.
- **Contrast:** low.
- **Key letters:**
  - double-storey a with a hooked top
  - double-storey g, as Archivo draws it (single-storey in the italics)
  - f with a hooked top and t with a hooked foot, their counters held open at
    every weight; the t's crossbar reaches as far right as its foot
  - round-bowled P and R
- **Figures:** cap-height, with proportional and tabular sets.

## Spacing

Snug and even, tuned for 12–14px text. f and t sit as far from a following
letter as n does. No pair of common characters may touch.

## Character set

Latin covering at least English, Western and Central European languages and
Vietnamese, plus ₦ and the common currency symbols, punctuation and arrows.

## OpenType features

Kerning, tabular figures, case-sensitive forms and localized forms.

## Deliverables

- TTF and WOFF2 for each style; a variable font as a later goal.
- A CSS file, the OFL licence and a FONTLOG of changes.
- A font book.

## Licence

SIL Open Font License 1.1. Copyright the Archivo Project Authors; modifications
copyright Chukwuemelie Ezenwa.

## Acceptance checks

- Metrics within 1% of the targets above.
- Stem weight within 3% of target.
- No collisions among common pairs.
- Coverage tests pass.
- Visual review in the Ezenwa Grotesk font book at 12px, 14px and 64px.
