# Ezenwa Grotesk

A contemporary grotesque sans for product user interfaces and brands. Compact
and dense, with closed apertures and a warm, slightly round rhythm. Built to
stay legible at 12–14px, with character at display sizes.

By Chukwuemelie Ezenwa. Built on [Archivo](https://github.com/Omnibus-Type/Archivo)
by Omnibus-Type.

## Files

- `fonts/`: TTF and WOFF2 for Light, Regular, Medium, Semibold and Bold, each
  with an italic, plus `ezenwa-grotesk.css`, `OFL.txt`, `FONTLOG.txt` and
  `fit-report.json` (every target and its result).
- `docs/font-book.pdf`: the specimen; `docs/preview.png`: the Regular page.
- `docs/comparisons/`: how the design was arrived at, beside Archivo.
- `SPEC.md`: the type specification.
- `base/`: the Archivo variable fonts the build starts from, with their licence.
- `fit.py`: the build, with its parts in `ezenwa/`: `targets.json` holds the
  measured targets and `spec.py` the letter and fitting constants.
- `check.py`: reports any character pair that touches.
- `test.py`: checks every style against `SPEC.md` (metrics, stems, figures,
  features, coverage, collisions, names) and runs fontbakery.
- `tools/font-book.js` and `tools/feature-sheet.js`: render the font book and
  a sheet of every OpenType feature off and on.
- `docs/fontbakery-report.md`: the latest fontbakery report.

## Use on the web

```css
@import url('fonts/ezenwa-grotesk.css');

body {
  font-family: 'Ezenwa Grotesk', system-ui, sans-serif;
}
```

## Rebuild

```bash
pip install fonttools brotli uharfbuzz
python3 fit.py
python3 check.py fonts/EzenwaGrotesk-Regular.ttf

# Before any release: every style against SPEC.md, plus fontbakery.
pip install fontbakery
python3 test.py --fontbakery

npm install playwright
node tools/font-book.js
node tools/feature-sheet.js
```

## Licence

The fonts are licensed under the SIL Open Font License 1.1 (`fonts/OFL.txt`).
Copyright the Archivo Project Authors; modifications copyright Chukwuemelie
Ezenwa. You may use, modify and redistribute them under the OFL; the fonts may
not be sold on their own.
