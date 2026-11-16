#!/usr/bin/env python3
"""Checks every built style against SPEC.md before a release.

Usage: python3 test.py [--fontbakery]

Prints one line per check and exits non-zero if any fails. With --fontbakery
it also runs the fontbakery universal profile and writes its report to
docs/fontbakery-report.md.
"""
import glob
import os
import subprocess
import sys

from fontTools.ttLib import TTFont
from pathops import Path, PathOp, op

from ezenwa.collisions import find_collisions
from ezenwa.measure import bounds

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, 'fonts')

# Targets copied from SPEC.md on purpose, so the build cannot pass by
# changing its own constants. Values in a 1000-unit em.
CAP, ASC, DESC = 640, 640, -170
F_TOP = 665          # the f's hook rises above the ascender
A_WIDTH = 1.0        # the a is as wide as the o
G_BOWL = 1.2         # the g's upper counter is at most this much wider than tall
X_HEIGHT = {'Light': 467, 'Regular': 470, 'Medium': 474, 'Semibold': 478, 'Bold': 480}
LC_STEM = {'Light': 63, 'Regular': 85, 'Medium': 123, 'Semibold': 148, 'Bold': 166}
UC_STEM = {'Light': 65, 'Regular': 89, 'Medium': 128, 'Semibold': 156, 'Bold': 174}
METRIC_TOLERANCE = 0.01
STEM_TOLERANCE = 0.03
FEATURES = {'kern', 'tnum', 'case', 'locl'}

COVERAGE = (
    [chr(c) for c in range(0x20, 0x7F)]
    + [chr(c) for c in range(0xA0, 0x100)]
    + [chr(c) for c in range(0x100, 0x180)]
    + [chr(c) for c in range(0x1EA0, 0x1EFA)]
    + list('ƠơƯư')
    + ['̀', '́', '̃', '̉', '̣']
    + list('₦€£¥$¢%‰')
    + list('‘’‚“”„–—…•·†‡')
    + list('←↑→↓↔↕')
)


def stem_at(gs, name, y):
    """Widest run of ink along a horizontal line at height y."""
    p = Path()
    gs[name].draw(p.getPen())
    strip = Path()
    strip.moveTo(-5000, y - 1)
    strip.lineTo(5000, y - 1)
    strip.lineTo(5000, y + 1)
    strip.lineTo(-5000, y + 1)
    strip.close()
    cut = op(p, strip, PathOp.INTERSECTION)
    return max((c.bounds[2] - c.bounds[0]) for c in cut.contours)


def g_bowl(gs, name):
    """Width over height of the g's upper counter: the inner contour that
    reaches highest."""
    p = Path()
    gs[name].draw(p.getPen())
    p.simplify()
    boxes = [c.bounds for c in p.contours]
    inside = lambda a, b: a[0] > b[0] and a[1] > b[1] and a[2] < b[2] and a[3] < b[3]
    holes = [b for b in boxes if any(inside(b, c) for c in boxes if c is not b)]
    top = max(holes, key=lambda b: b[3])
    return (top[2] - top[0]) / (top[3] - top[1])


def within(value, target, tolerance):
    return abs(value - target) <= abs(target) * tolerance


def check_font(path):
    font = TTFont(path)
    gs, cmap = font.getGlyphSet(), font.getBestCmap()
    g = lambda ch: cmap[ord(ch)]
    style = font['name'].getDebugName(17) or 'Regular'
    italic = 'Italic' in style
    weight = style.replace(' Italic', '').replace('Italic', '') or 'Regular'
    results = []

    def record(name, ok, detail):
        results.append((name, ok, detail))

    cap = bounds(gs, g('H'))[3]
    xh = bounds(gs, g('x'))[3]
    asc = bounds(gs, g('l'))[3]
    desc = bounds(gs, g('p'))[1]
    record('cap height', within(cap, CAP, METRIC_TOLERANCE), f'{cap:.0f} (target {CAP})')
    record('x-height', within(xh, X_HEIGHT[weight], METRIC_TOLERANCE), f'{xh:.0f} (target {X_HEIGHT[weight]})')
    record('ascender', within(asc, ASC, METRIC_TOLERANCE), f'{asc:.0f} (target {ASC})')
    record('descender', within(desc, DESC, METRIC_TOLERANCE), f'{desc:.0f} (target {DESC})')

    if not italic:
        lc = bounds(gs, g('l'))
        uc = bounds(gs, g('I'))
        lc_w, uc_w = lc[2] - lc[0], uc[2] - uc[0]
        record('lowercase stem', within(lc_w, LC_STEM[weight], STEM_TOLERANCE), f'{lc_w:.0f} (target {LC_STEM[weight]})')
        record('capital stem', within(uc_w, UC_STEM[weight], STEM_TOLERANCE), f'{uc_w:.0f} (target {UC_STEM[weight]})')

    f_top = bounds(gs, g('f'))[3]
    record('f top', within(f_top, F_TOP, METRIC_TOLERANCE), f'{f_top:.0f} (target {F_TOP})')

    if not italic:
        a, o = bounds(gs, g('a')), bounds(gs, g('o'))
        ratio = (a[2] - a[0]) / (o[2] - o[0])
        record('a as wide as o', within(ratio, A_WIDTH, METRIC_TOLERANCE), f'{ratio:.3f} of the o')
        bowl = g_bowl(gs, g('g'))
        record('g bowl', bowl <= G_BOWL + 0.01, f'counter {bowl:.2f} wide per tall (at most {G_BOWL})')

    tabular = [n for n in font.getGlyphOrder() if n.endswith('.tf')]
    widths = {font['hmtx'][n][0] for n in tabular}
    record('tabular figures share one width', len(widths) == 1, f'{sorted(widths)}')
    y = cap * 0.45
    prop, tab = stem_at(gs, 'one', y), stem_at(gs, 'one.tf', y)
    record('tabular figures match proportional weight', within(tab, prop, STEM_TOLERANCE), f'1: {prop:.0f} vs 1.tf: {tab:.0f}')

    present = {fr.FeatureTag for t in ('GSUB', 'GPOS') if t in font for fr in font[t].table.FeatureList.FeatureRecord}
    missing = FEATURES - present
    record('OpenType features', not missing, 'all present' if not missing else f'missing {sorted(missing)}')

    absent = [c for c in COVERAGE if ord(c) not in cmap]
    record('character coverage', not absent, f'{len(COVERAGE)} characters' if not absent else f'missing {"".join(absent)}')

    hits = find_collisions(path)
    record('no touching pairs', not hits, f'{len(hits)} pairs')

    names = font['name']
    family = names.getDebugName(16) or names.getDebugName(1)
    copyright_ = names.getDebugName(0) or ''
    record('family name', family == 'Ezenwa Grotesk', family)
    record('copyright credits Archivo and Ezenwa', 'Archivo' in copyright_ and 'Ezenwa' in copyright_, copyright_[:60] + '…')
    return results


def main():
    paths = sorted(glob.glob(os.path.join(FONTS, '*.ttf')))
    failed = 0
    for path in paths:
        print(f'\n{os.path.basename(path)}')
        for name, ok, detail in check_font(path):
            print(f'  {"PASS" if ok else "FAIL"}  {name}: {detail}')
            failed += not ok
    if '--fontbakery' in sys.argv:
        report = os.path.join(HERE, 'docs', 'fontbakery-report.md')
        print(f'\nRunning fontbakery; report in {os.path.relpath(report, HERE)}')
        subprocess.run(['fontbakery', 'check-universal', '--ghmarkdown', report, *paths],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f'\n{"All checks passed." if not failed else f"{failed} check(s) failed."}')
    sys.exit(1 if failed else 0)


if __name__ == '__main__':
    main()
