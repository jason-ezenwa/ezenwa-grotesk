"""Letters rebuilt from Archivo's own shapes. Each is drawn upright (italics
are slanted back first) and slanted again afterwards."""
import math
import unicodedata

from pathops import PathOp, op

from .measure import bounds
from .outlines import BIG, box, drop_specks, path_of, put_glyph, transform_path
from .spec import (F_DEPTH, F_JOIN, F_MIN_WIDTH, F_REACH, F_TERMINAL, MIN_COUNTER, T_DEPTH,
                   T_JOIN, T_MIN_WIDTH, T_REACH, T_TERMINAL)


def _o_contours(o):
    return sorted(o.contours, key=lambda c: -abs(c.area))[:2]


def o_strokes(o):
    """The o's stroke thickness at the bottom and at the top."""
    (_, oy0, _, oy1), (_, iy0, _, iy1) = (c.bounds for c in _o_contours(o))
    return iy0 - oy0, oy1 - iy1


def ring_from_o(o, x0, y0, x1, y1, left, right, bottom, top):
    """The o's outer and inner contours fitted into a box with the given
    stroke thicknesses, so the ring keeps the o's curves."""
    outer, inner = _o_contours(o)

    def onto(c, tx0, ty0, tx1, ty1):
        bx0, by0, bx1, by1 = c.bounds
        sx, sy = (tx1 - tx0) / (bx1 - bx0), (ty1 - ty0) / (by1 - by0)
        return transform_path(c, (sx, 0, 0, sy, tx0 - bx0 * sx, ty0 - by0 * sy))

    return op(onto(outer, x0, y0, x1, y1),
              onto(inner, x0 + left, y0 + bottom, x1 - right, y1 - top), PathOp.DIFFERENCE)


def _stem(path, y0, y1):
    """Left and right edges of the ink between heights y0 and y1."""
    x0, _, x1, _ = op(path, box(-BIG, y0, BIG, y1), PathOp.INTERSECTION).bounds
    return x0, x1


def _hook(sx0, stem_w, x1, stroke):
    """Right end and terminal thickness of a hook spanning sx0 to x1. At heavy
    weights the terminal thins toward the o's horizontal stroke, and the hook
    widens if it must, so its counter stays at least MIN_COUNTER stems wide."""
    counter = MIN_COUNTER * stem_w
    right = min(0.9 * stem_w, max(stroke, x1 - sx0 - stem_w - counter))
    return max(x1, sx0 + stem_w + right + counter), right


def build_f(f, o, xh):
    """f with a hook cut from the o, ending in a near-horizontal cut."""
    top = f.bounds[3]
    sx0, sx1 = _stem(f, xh + 15, xh + 45)
    bar_right = _stem(f, xh - 25, xh - 5)[1]
    stem_w = sx1 - sx0
    _, top_w = o_strokes(o)
    # The join drops at heavy weights so the counter stays MIN_COUNTER stems tall.
    yc = min(xh + (top - xh) * F_JOIN, top - top_w - MIN_COUNTER * stem_w)
    x1 = max(bar_right + F_REACH * stem_w, sx0 + F_MIN_WIDTH * (o.bounds[2] - o.bounds[0]))
    x1, right = _hook(sx0, stem_w, x1, top_w)
    ring = ring_from_o(o, sx0, 2 * yc - top, x1, top, stem_w, right, top_w, top_w)
    hook = op(ring, box(-BIG, yc, BIG, BIG), PathOp.INTERSECTION)
    counter_top = top - top_w
    cut = min(yc + (top - yc) * F_TERMINAL, counter_top - F_DEPTH * (counter_top - yc))
    hook = op(hook, box((sx0 + x1) / 2, -BIG, BIG, cut), PathOp.DIFFERENCE)
    body = op(f, box(-BIG, -BIG, BIG, max(yc, xh)), PathOp.INTERSECTION)
    return op(body, hook, PathOp.UNION)


def build_t(t, o, xh):
    """t with a foot cut from the o, ending in a near-horizontal cut, and a
    crossbar that reaches as far right as the foot."""
    sx0, sx1 = _stem(t, xh * 0.45, xh * 0.55)
    bar_right = _stem(t, xh - 25, xh - 5)[1]
    stem_w = sx1 - sx0
    bottom_w, _ = o_strokes(o)
    bottom = o.bounds[1]
    # The join rises at heavy weights so the counter stays MIN_COUNTER stems tall.
    yc = max(xh * T_JOIN, bottom + bottom_w + MIN_COUNTER * stem_w)
    x1 = max(bar_right + T_REACH * stem_w, sx0 + T_MIN_WIDTH * (o.bounds[2] - o.bounds[0]))
    x1, right = _hook(sx0, stem_w, x1, bottom_w)
    ring = ring_from_o(o, sx0, bottom, x1, 2 * yc - bottom, stem_w, right, bottom_w, bottom_w)
    foot = op(ring, box(-BIG, -BIG, BIG, yc), PathOp.INTERSECTION)
    counter_bottom = bottom + bottom_w
    cut = max(yc - (yc - bottom) * T_TERMINAL, counter_bottom + T_DEPTH * (yc - counter_bottom))
    foot = op(foot, box((sx0 + x1) / 2, cut, BIG, BIG), PathOp.DIFFERENCE)
    body = op(t, box(-BIG, yc, BIG, BIG), PathOp.INTERSECTION)
    _, bar_y0, _, bar_y1 = op(t, box(sx1 + 5, xh * 0.6, BIG, BIG), PathOp.INTERSECTION).bounds
    bar = box(sx1, bar_y0, foot.bounds[2], bar_y1)
    return op(op(body, foot, PathOp.UNION), bar, PathOp.UNION)


def _rebuild_accented(font, cmap, old, new):
    """Swaps each accented form's old base letter for the new one."""
    rev = {n: cp for cp, n in cmap.items()}
    rebuilt_names = {cmap[ord(ch)] for ch in old}
    for name in font.getGlyphOrder():
        gl = font['glyf'][name]
        if gl.isComposite() or gl.numberOfContours <= 0 or name in rebuilt_names:
            continue
        cp = rev.get(name) or rev.get(name.split('.')[0])
        if cp is None:
            continue
        base = unicodedata.normalize('NFD', chr(cp))[0]
        if base not in old or base == chr(cp):
            continue
        glyph = path_of(font, name)
        if abs(op(glyph, old[base], PathOp.INTERSECTION).area) < 0.97 * abs(old[base].area):
            continue  # the base letter sits elsewhere in this glyph
        marks = drop_specks(op(glyph, old[base], PathOp.DIFFERENCE))
        result = op(marks, new[base], PathOp.UNION)
        result.simplify(fix_winding=True, keep_starting_points=False)
        put_glyph(font, name, result)


def _drop_f_ligatures(font, f):
    for lookup in font['GSUB'].table.LookupList.Lookup:
        for st in lookup.SubTable:
            st = getattr(st, 'ExtSubTable', st)
            if hasattr(st, 'ligatures') and f in st.ligatures:
                del st.ligatures[f]


def letter_edits(font, italic):
    """Rebuilds f and t, carries the changes into the accented forms and
    drops the f ligatures, which keep the old f."""
    cmap = font.getBestCmap()
    name = {ch: cmap[ord(ch)] for ch in 'ftox'}
    edited = 'ft'
    old = {ch: path_of(font, name[ch]) for ch in edited}

    tan = math.tan(math.radians(-font['post'].italicAngle)) if italic else 0
    upright, slanted = (1, 0, -tan, 1, 0, 0), (1, 0, tan, 1, 0, 0)
    get = lambda ch: transform_path(path_of(font, name[ch]), upright)
    put = lambda ch, path: put_glyph(font, name[ch], transform_path(path, slanted))
    o, xh = get('o'), bounds(font.getGlyphSet(), name['x'])[3]
    put('f', build_f(get('f'), o, xh))
    put('t', build_t(get('t'), o, xh))

    _rebuild_accented(font, cmap, old, {ch: path_of(font, name[ch]) for ch in edited})
    _drop_f_ligatures(font, name['f'])
