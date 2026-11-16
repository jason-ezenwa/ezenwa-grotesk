"""Outline edits: sharp corners, rounder curves, and path helpers."""
import math

from fontTools.cu2qu import curve_to_quadratic
from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib.tables._g_l_y_f import GlyphCoordinates
from pathops import Path

from .spec import CORNER

BIG = 5000


# Contours as lists of ((x, y), on_curve)

def _contours(glyph):
    coords, flags, start = list(glyph.coordinates), glyph.flags, 0
    for end in glyph.endPtsOfContours:
        yield [(coords[k], bool(flags[k] & 1)) for k in range(start, end + 1)]
        start = end + 1


def _set_contours(glyph, contours, glyf):
    coords, flags, ends = [], [], []
    for pts in contours:
        for p, on in pts:
            coords.append(p)
            flags.append(1 if on else 0)
        ends.append(len(coords) - 1)
    glyph.coordinates = GlyphCoordinates(coords)
    glyph.flags = bytearray(flags)
    glyph.endPtsOfContours = ends
    glyph.recalcBounds(glyf)


def map_contours(font, fn, names=None):
    """Replaces every contour of every simple glyph with fn(contour)."""
    glyf = font['glyf']
    for name in names or font.getGlyphOrder():
        gl = glyf[name]
        if not gl.isComposite() and gl.numberOfContours > 0:
            _set_contours(gl, [fn(pts) for pts in _contours(gl)], glyf)


# Sharp corners

def _intersect(p1, d1, p2, d2):
    den = d1[0] * d2[1] - d1[1] * d2[0]
    if abs(den) < 1e-9:
        return None
    t = ((p2[0] - p1[0]) * d2[1] - (p2[1] - p1[1]) * d2[0]) / den
    return (p1[0] + d1[0] * t, p1[1] + d1[1] * t)


def _sharpen_one(pts):
    """Finds one small rounded corner (on-curve, off-curves, on-curve, a short
    chord apart) and replaces it with the point where its edges meet."""
    n = len(pts)
    for i in range(n):
        a, a_on = pts[i]
        if not a_on:
            continue
        j, offs = (i + 1) % n, []
        while not pts[j][1] and len(offs) < 3:
            offs.append(j)
            j = (j + 1) % n
        if not offs or not pts[j][1]:
            continue
        b = pts[j][0]
        if math.dist(a, b) >= CORNER:
            continue
        prev, nxt = pts[(i - 1) % n][0], pts[(j + 1) % n][0]
        d1 = (a[0] - prev[0], a[1] - prev[1])
        d2 = (nxt[0] - b[0], nxt[1] - b[1])
        l1, l2 = math.hypot(*d1), math.hypot(*d2)
        if l1 < 1 or l2 < 1:
            continue
        if (d1[0] * d2[0] + d1[1] * d2[1]) / (l1 * l2) > 0.7:
            continue  # nearly straight: a real curve, not a corner
        c = _intersect(a, d1, b, d2)
        if c is None or math.dist(c, a) > CORNER or math.dist(c, b) > CORNER:
            continue
        drop = set(offs + [j])
        return [((round(c[0]), round(c[1])), True) if k == i else p
                for k, p in enumerate(pts) if k not in drop]
    return None


def _sharpen_contour(pts):
    pts = [p for k, p in enumerate(pts) if p[0] != pts[k - 1][0] or len(pts) == 1]
    while len(pts) >= 5:
        sharper = _sharpen_one(pts)
        if sharper is None:
            break
        pts = sharper
    return pts


def sharpen_corners(font):
    map_contours(font, _sharpen_contour)


# Rounder curves

def _arc_samples(a, offs, b, per=12):
    """Points along a TrueType arc from on-curve a through offs to on-curve b."""
    segs, start = [], a
    for i, q in enumerate(offs):
        end = b if i == len(offs) - 1 else ((q[0] + offs[i + 1][0]) / 2, (q[1] + offs[i + 1][1]) / 2)
        segs.append((start, q, end))
        start = end
    pts = []
    for p0, q, p1 in segs:
        for k in range(per):
            u = k / per
            pts.append(((1 - u) ** 2 * p0[0] + 2 * (1 - u) * u * q[0] + u * u * p1[0],
                        (1 - u) ** 2 * p0[1] + 2 * (1 - u) * u * q[1] + u * u * p1[1]))
    pts.append(b)
    return pts


def _fit_cubic(pts, a, b, t1, t2):
    """Least-squares handle lengths for a cubic from a to b that leaves along
    unit tangent t1 and arrives along t2."""
    lens = [0]
    for p, q in zip(pts, pts[1:]):
        lens.append(lens[-1] + math.dist(p, q))
    s11 = s12 = s22 = r1 = r2 = 0
    for p, length in zip(pts, lens):
        u = length / lens[-1]
        b0, b1, b2, b3 = (1 - u) ** 3, 3 * (1 - u) ** 2 * u, 3 * (1 - u) * u * u, u ** 3
        base = ((b0 + b1) * a[0] + (b2 + b3) * b[0], (b0 + b1) * a[1] + (b2 + b3) * b[1])
        c1 = (b1 * t1[0], b1 * t1[1])
        c2 = (-b2 * t2[0], -b2 * t2[1])
        r = (p[0] - base[0], p[1] - base[1])
        s11 += c1[0] ** 2 + c1[1] ** 2
        s12 += c1[0] * c2[0] + c1[1] * c2[1]
        s22 += c2[0] ** 2 + c2[1] ** 2
        r1 += c1[0] * r[0] + c1[1] * r[1]
        r2 += c2[0] * r[0] + c2[1] * r[1]
    det = s11 * s22 - s12 * s12
    if abs(det) < 1e-9:
        return None
    return (r1 * s22 - r2 * s12) / det, (s11 * r2 - s12 * r1) / det


def _round_arc(a, offs, b, tension):
    """Refits a roughly right-angled arc as one cubic with its handles scaled
    by tension (below 1 is rounder) and returns its new off-curve points, or
    None to leave it alone. End points and tangents never move."""
    d1 = (offs[0][0] - a[0], offs[0][1] - a[1])
    d2 = (b[0] - offs[-1][0], b[1] - offs[-1][1])
    n1, n2 = math.hypot(*d1), math.hypot(*d2)
    if n1 < 1 or n2 < 1 or math.dist(a, b) < 40:
        return None
    if abs((d1[0] * d2[0] + d1[1] * d2[1]) / (n1 * n2)) > 0.5:
        return None
    t1, t2 = (d1[0] / n1, d1[1] / n1), (d2[0] / n2, d2[1] / n2)
    handles = _fit_cubic(_arc_samples(a, offs, b), a, b, t1, t2)
    if not handles or handles[0] <= 0 or handles[1] <= 0:
        return None
    h1, h2 = handles[0] * tension, handles[1] * tension
    cubic = [a, (a[0] + t1[0] * h1, a[1] + t1[1] * h1), (b[0] - t2[0] * h2, b[1] - t2[1] * h2), b]
    return [(round(x), round(y)) for x, y in curve_to_quadratic(cubic, 0.5)[1:-1]]


def _round_contour(pts, tension):
    n = len(pts)
    ons = [i for i, (_, on) in enumerate(pts) if on]
    if len(ons) < 2:
        return pts
    replace = {}
    for idx, i in enumerate(ons):
        j = ons[(idx + 1) % len(ons)]
        offs, k = [], (i + 1) % n
        while k != j:
            offs.append(k)
            k = (k + 1) % n
        if offs:
            new = _round_arc(pts[i][0], [pts[k][0] for k in offs], pts[j][0], tension)
            if new:
                replace[i] = (offs, new)
    if not replace:
        return pts
    skip = {k for offs, _ in replace.values() for k in offs}
    out = []
    for i, p in enumerate(pts):
        if i in skip:
            continue
        out.append(p)
        if i in replace:
            out.extend((q, False) for q in replace[i][1])
    return out


def round_curves(font, tension, names=None):
    map_contours(font, lambda pts: _round_contour(pts, tension), names)


# Paths

def path_of(font, name):
    p = Path()
    font.getGlyphSet()[name].draw(p.getPen())
    return p


def transform_path(path, m):
    out = Path()
    path.draw(TransformPen(out.getPen(), m))
    return out


def box(x0, y0, x1, y1):
    p = Path()
    p.moveTo(x0, y0)
    p.lineTo(x1, y0)
    p.lineTo(x1, y1)
    p.lineTo(x0, y1)
    p.close()
    return p


def drop_specks(path, min_area=400):
    """Removes slivers left over by a boolean operation."""
    out = Path()
    pen = out.getPen()
    for c in path.contours:
        if abs(c.area) >= min_area:
            c.draw(pen)
    return out


def _dedupe(pts):
    """Collapses repeated points, keeping on-curve if either was."""
    kept = []
    for p, on in pts:
        if kept and kept[-1][0] == p:
            kept[-1] = (p, kept[-1][1] or on)
        else:
            kept.append((p, on))
    if len(kept) > 1 and kept[0][0] == kept[-1][0]:
        kept[0] = (kept[0][0], kept[0][1] or kept[-1][1])
        kept.pop()
    return kept


def put_glyph(font, name, path):
    """Stores a path as a TrueType glyph, keeping its advance."""
    pen = TTGlyphPen(None)
    path.draw(Cu2QuPen(pen, max_err=1))
    glyph = pen.glyph()
    glyf = font['glyf']
    _set_contours(glyph, [_dedupe(pts) for pts in _contours(glyph)], glyf)
    glyf[name] = glyph
    glyph.recalcBounds(glyf)
    font['hmtx'][name] = (font['hmtx'][name][0], getattr(glyph, 'xMin', 0))
