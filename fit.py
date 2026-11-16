#!/usr/bin/env python3
"""Builds Ezenwa Grotesk by fitting Archivo (OFL) to the targets in
ezenwa/targets.json. Every outline is Archivo's.

Usage: python3 fit.py [Style ...]
"""
import json
import os
import sys

from ezenwa.classes import base_letters, figure_variants, glyph_classes
from ezenwa.collisions import match_open_gaps, settle_collisions
from ezenwa.finish import finish, postscript_name, set_names
from ezenwa.fitting import (ITALIC, ROMAN, base_font, em_scale, fit_spacing, fit_widths,
                         remap_vertical, solve_location, solve_roundness)
from ezenwa.letters import letter_edits, narrow_letters
from ezenwa.measure import fullness, measure
from ezenwa.outlines import round_curves
from ezenwa.spec import GROUPS, ROUNDNESS, STYLES, SUBCLASS
from ezenwa.targets import targets

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fonts')


def check_against(font, ref):
    """Each measurement beside its target, for fit-report.json."""
    final = measure(font)
    return {
        **{key: [round(final[key]), round(ref[key])] for key in ('cap', 'xh', 'asc', 'desc')},
        'ink': [round(final['ink'], 3), round(ref['ink'], 3)],
        'capstem': [round(final['capstem']), round(ref['capstem'])],
        'width_delta_pct': {c: round((final['width'][c] / ref['width'][c] - 1) * 100, 1)
                            for c in SUBCLASS},
        'space_delta_units': {c: round(final['space'][c] - ref['space'][c]) for c in SUBCLASS},
    }


def build(style, weight, italic, k, roman=None):
    """Builds one style. Italics reuse the roman's axis locations, roundness,
    widths and spacing: slanted bounds cannot be compared with the
    reference's differently slanted ones."""
    ref, upright = targets(style, italic), targets(style, False)

    if roman:
        locs = roman['locs']
    else:
        locs = {g: solve_location(k, upright['groups'][g]['width'], upright['groups'][g]['stem'], chars)
                for g, chars in GROUPS.items()}
    font = base_font(ITALIC if italic else ROMAN, locs, k)

    cur = measure(font)
    case, sub = glyph_classes(font)
    variants = figure_variants(font)
    remap_vertical(font, case, (cur['desc'], cur['xh'], cur['asc']),
                   (ref['desc'], ref['xh'], ref['asc']))

    if roman:
        tension = roman['roundness']
    else:
        base_full = fullness(font, 'o')
        tension = solve_roundness(font, base_full + ROUNDNESS * (upright['o_fullness'] - base_full))
    round_curves(font, tension)
    letter_edits(font, italic)

    report = {'style': style, 'italic': italic, 'locs': locs, 'roundness': tension}
    report['width'] = fit_widths(font, sub, variants, ref, roman)
    report['space'] = fit_spacing(font, sub, ref, roman)
    report['narrowed'] = narrow_letters(font, italic)

    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, postscript_name(style, italic))
    report['open_gaps'] = match_open_gaps(font, f'{path}.ttf', base_letters(font))

    hmtx, cmap = font['hmtx'], font.getBestCmap()
    hmtx[cmap[32]] = (ref['word_space'], 0)
    font['OS/2'].sxHeight, font['OS/2'].sCapHeight = round(ref['xh']), round(ref['cap'])
    set_names(font, style, weight, italic)

    report['check'] = check_against(font, ref)
    report['opened_pairs'] = settle_collisions(font, f'{path}.ttf')
    finish(font, style, weight, italic)
    font.save(f'{path}.ttf')
    font.flavor = 'woff2'
    font.save(f'{path}.woff2')
    print(os.path.basename(path), json.dumps(report['check']))
    return report


def main():
    only = sys.argv[1:]
    k = em_scale()
    reports = []
    for style, weight in STYLES:
        if only and style not in only:
            continue
        roman = build(style, weight, False, k)
        reports += [roman, build(style, weight, True, k, roman)]
    with open(os.path.join(OUT, 'fit-report.json'), 'w') as fh:
        json.dump(reports, fh, indent=2)


if __name__ == '__main__':
    main()
