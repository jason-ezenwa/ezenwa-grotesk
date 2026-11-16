"""Measurements of a font."""
from fontTools.pens.areaPen import AreaPen
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.recordingPen import DecomposingRecordingPen, RecordingPen

from .spec import LC, SUBCLASS


def bounds(gs, name):
    pen = BoundsPen(gs)
    gs[name].draw(pen)
    return pen.bounds


def measure(font):
    """Vertical metrics, capital stem, and per-subclass mean width and bearings."""
    gs, cmap = font.getGlyphSet(), font.getBestCmap()
    g = lambda ch: cmap[ord(ch)]
    i_box = bounds(gs, g('I'))
    m = {
        'cap': bounds(gs, g('H'))[3],
        'xh': bounds(gs, g('x'))[3],
        'asc': bounds(gs, g('l'))[3],
        'desc': bounds(gs, g('p'))[1],
        'capstem': i_box[2] - i_box[0],
        'width': {}, 'space': {}, 'lsb': {}, 'rsb': {},
    }
    for cls, chars in SUBCLASS.items():
        boxes = [(bounds(gs, g(ch)), gs[g(ch)].width) for ch in chars]
        n = len(chars)
        m['width'][cls] = sum(b[2] - b[0] for b, _ in boxes) / n
        m['lsb'][cls] = sum(b[0] for b, _ in boxes) / n
        m['rsb'][cls] = sum(adv - b[2] for b, adv in boxes) / n
        m['space'][cls] = m['lsb'][cls] + m['rsb'][cls]
    ink = area = 0
    for ch in LC:
        pen = AreaPen(gs)
        gs[g(ch)].draw(pen)
        ink += abs(pen.value)
        area += gs[g(ch)].width * m['xh']
    m['ink'] = ink / area
    return m


def group_stats(font, chars):
    """Mean ink width of chars, and the stem of l (lowercase) or I (otherwise)."""
    gs, cmap = font.getGlyphSet(), font.getBestCmap()
    boxes = [bounds(gs, cmap[ord(c)]) for c in chars]
    x0, _, x1, _ = bounds(gs, cmap[ord('l' if chars == LC else 'I')])
    return sum(b[2] - b[0] for b in boxes) / len(boxes), x1 - x0


def fullness(font, char):
    """Area of a glyph's largest contour over its bounding box: 0.785 for an
    ellipse, approaching 1 as the shape squares off."""
    gs = font.getGlyphSet()
    rec = DecomposingRecordingPen(gs)
    gs[font.getBestCmap()[ord(char)]].draw(rec)
    best_ratio, best_area, contour = 0, 0, []
    for op, args in rec.value:
        contour.append((op, args))
        if op not in ('closePath', 'endPath'):
            continue
        part = RecordingPen()
        part.value = contour
        area, box = AreaPen(), BoundsPen(None)
        part.replay(area)
        part.replay(box)
        x0, y0, x1, y1 = box.bounds
        if abs(area.value) > best_area:
            best_ratio, best_area = abs(area.value) / ((x1 - x0) * (y1 - y0)), abs(area.value)
        contour = []
    return best_ratio
