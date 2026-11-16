"""Fits Archivo to the targets: axis locations, proportions, widths, spacing."""
import copy
import os

from fontTools import subset
from fontTools.ttLib import TTFont
from fontTools.ttLib.scaleUpem import scale_upem
from fontTools.varLib import instancer

from .classes import figure_variants, glyph_classes
from .measure import fullness, group_stats, measure
from .outlines import round_curves, sharpen_corners
from .spec import CAP, FIG, LC, MAX_STRETCH, OVERSHOOT_BAND, SUBCLASS, UC

BASE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'base')
ROMAN, ITALIC = 'Archivo[wdth,wght].ttf', 'Archivo-Italic[wdth,wght].ttf'
HINTING_TABLES = ('fpgm', 'prep', 'cvt ', 'hdmx', 'LTSH', 'VDMX', 'STAT')


def instance(src, loc, k=None, glyphs=None):
    """A static Archivo at loc, scaled by k, with sharp corners and no hinting."""
    vf = TTFont(os.path.join(BASE, src))
    if glyphs:
        opts = subset.Options()
        opts.notdef_outline = True
        opts.layout_features = []
        sub = subset.Subsetter(opts)
        sub.populate(text=glyphs)
        sub.subset(vf)
    font = instancer.instantiateVariableFont(vf, loc)
    for tag in HINTING_TABLES:
        if tag in font:
            del font[tag]
    sharpen_corners(font)
    if k:
        scale_upem(font, round(1000 * k))
        font['head'].unitsPerEm = 1000
    return font


def em_scale():
    """Scale that puts Archivo's cap height on CAP, to three decimals."""
    return round(1000 * CAP / measure(instance(ROMAN, {'wght': 400, 'wdth': 100}))['cap']) / 1000


def solve_location(k, target_w, target_stem, chars):
    """The (wght, wdth) where chars have the target mean width and stem."""
    probe = LC + UC + FIG + 'HIlxp'

    def stats(wght, wdth):
        return group_stats(instance(ROMAN, {'wght': wght, 'wdth': wdth}, k, probe), chars)

    wght, wdth = 400, 100
    for _ in range(3):
        lo, hi = 100, 900
        for _ in range(11):
            wght = (lo + hi) / 2
            lo, hi = (wght, hi) if stats(wght, wdth)[1] < target_stem else (lo, wght)
        lo, hi = 62, 125
        for _ in range(11):
            wdth = (lo + hi) / 2
            lo, hi = (wdth, hi) if stats(wght, wdth)[0] < target_w else (lo, wdth)
    return round(wght, 1), round(wdth, 1)


def solve_roundness(font, target):
    """The curve tension that brings the o's fullness to target."""
    name = font.getBestCmap()[ord('o')]
    original = copy.deepcopy(font['glyf'][name])
    lo, hi = 0.6, 1.0
    for _ in range(14):
        mid = (lo + hi) / 2
        font['glyf'][name] = copy.deepcopy(original)
        round_curves(font, mid, [name])
        lo, hi = (lo, mid) if fullness(font, 'o') > target else (mid, hi)
    font['glyf'][name] = original
    return round((lo + hi) / 2, 4)


def clamp(k):
    return max(1 - MAX_STRETCH, min(1 + MAX_STRETCH, k))


def _piecewise(src, dst):
    """Maps descender, x-height and ascender from src to dst. Overshoots stay
    at the x-height scale so round letters keep their overshoot."""
    d0, x0, a0 = src
    d1, x1, a1 = dst
    s = x1 / x0

    def f(y):
        if -OVERSHOOT_BAND <= y <= x0 + OVERSHOOT_BAND:
            return y * s if y <= x0 else x1 + (y - x0) * s
        if y > x0 + OVERSHOOT_BAND:
            ys, yt = x0 + OVERSHOOT_BAND, x1 + OVERSHOOT_BAND * s
            return yt + (y - ys) * (a1 - yt) / (a0 - ys)
        ys, yt = -OVERSHOOT_BAND, -OVERSHOOT_BAND * s
        return yt + (y - ys) * (d1 - yt) / (d0 - ys)
    return f


def remap_vertical(font, case, src, dst):
    """Moves the lowercase onto new descender, x-height and ascender."""
    f = _piecewise(src, dst)
    glyf = font['glyf']
    for name in font.getGlyphOrder():
        if case[name] != 'lc':
            continue
        gl = glyf[name]
        if gl.isComposite():
            for c in gl.components:
                if case.get(c.glyphName) != 'lc' and c.y:
                    c.y = round(f(c.y))
        elif gl.numberOfContours > 0:
            gl.coordinates = type(gl.coordinates)([(x, round(f(y))) for x, y in gl.coordinates])
        gl.recalcBounds(glyf)


def scale_x(font, names, k):
    glyf, hmtx = font['glyf'], font['hmtx']
    for name in sorted(names, key=lambda n: glyf[n].isComposite()):
        gl = glyf[name]
        if gl.isComposite():
            for c in gl.components:
                c.x = round(c.x * k)
        elif gl.numberOfContours > 0:
            gl.coordinates = type(gl.coordinates)([(round(x * k), y) for x, y in gl.coordinates])
        gl.recalcBounds(glyf)
        hmtx[name] = (round(hmtx[name][0] * k), getattr(gl, 'xMin', 0))


def respace(font, names, k, add=(0, 0)):
    """Scales both side bearings by k and adds add. A composite as wide as its
    base glyph stays as wide."""
    glyf, hmtx = font['glyf'], font['hmtx']
    old_adv = {n: hmtx[n][0] for n in font.getGlyphOrder()}

    def bearings(gl, name):
        lsb, rsb = gl.xMin, hmtx[name][0] - gl.xMax
        return lsb, round(lsb * k + add[0]), round(rsb * k + add[1])

    for name in names:
        gl = glyf[name]
        if gl.isComposite():
            continue
        gl.recalcBounds(glyf)
        if gl.numberOfContours <= 0:
            continue
        lsb, nl, nr = bearings(gl, name)
        gl.coordinates = type(gl.coordinates)([(x + nl - lsb, y) for x, y in gl.coordinates])
        gl.recalcBounds(glyf)
        hmtx[name] = (gl.xMax - gl.xMin + nl + nr, gl.xMin)

    for name in names:
        gl = glyf[name]
        if not gl.isComposite():
            continue
        base = gl.components[0].glyphName
        gl.recalcBounds(glyf)
        if old_adv[name] == old_adv[base] and gl.components[0].x == 0:
            hmtx[name] = (hmtx[base][0], gl.xMin)
            continue
        lsb, nl, nr = bearings(gl, name)
        for c in gl.components:
            c.x += nl - lsb
        gl.recalcBounds(glyf)
        hmtx[name] = (gl.xMax - gl.xMin + nl + nr, gl.xMin)


def base_font(src, locs, k):
    """Archivo with each case group taken from its own axis location."""
    font = instance(src, {'wght': locs['lc'][0], 'wdth': locs['lc'][1]}, k)
    case, sub = glyph_classes(font)
    variants = figure_variants(font)
    for group in ('uc', 'fig'):
        other = instance(src, {'wght': locs[group][0], 'wdth': locs[group][1]}, k)
        for n in font.getGlyphOrder():
            if group == 'uc':
                wanted = case[n] == 'uc'
            else:
                wanted = sub.get(n) == 'figures' or n in variants
            if wanted and not font['glyf'][n].isComposite() and n in other['glyf'].glyphs:
                font['glyf'][n] = other['glyf'][n]
                font['hmtx'][n] = other['hmtx'][n]
    return font


def fit_widths(font, sub, variants, ref, roman):
    cur = measure(font)
    factors = {}
    for cls in SUBCLASS:
        k = roman['width'][cls] if roman else clamp(ref['width'][cls] / cur['width'][cls])
        names = [n for n, c in sub.items() if c == cls]
        if cls == 'figures':
            names += sorted(variants - set(names))
        scale_x(font, names, k)
        factors[cls] = round(k, 4)
    return factors


def fit_spacing(font, sub, ref, roman):
    """Scales each class's bearings to the reference. Where bearings are near
    zero or negative a ratio means nothing, so each side moves by the difference."""
    cur = measure(font)
    factors = {}
    for cls in SUBCLASS:
        if roman:
            k, add = roman['space'][cls]
        elif min(ref['space'][cls], cur['space'][cls]) > 20:
            k, add = ref['space'][cls] / cur['space'][cls], (0, 0)
        else:
            k, add = 1, (ref['lsb'][cls] - cur['lsb'][cls], ref['rsb'][cls] - cur['rsb'][cls])
        respace(font, [n for n, c in sub.items() if c == cls], k, add)
        factors[cls] = (round(k, 4), (round(add[0], 1), round(add[1], 1)))
    return factors
