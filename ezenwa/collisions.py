"""Finds character pairs whose outlines touch, and kerns them apart."""
import itertools

import uharfbuzz as hb
from fontTools.otlLib.builder import buildPairPosGlyphs, buildValue
from fontTools.pens.basePen import BasePen
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables import otTables as ot

from .spec import CLEARANCE

CHARS = ('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
         '.,:;!?\'"()[]-/&@₦$€£%#*+=')
PROFILE_BAND = 10


class ProfilePen(BasePen):
    """Records the leftmost and rightmost ink in each horizontal band."""

    def __init__(self, gs):
        super().__init__(gs)
        self.left, self.right = {}, {}
        self.cur = (0, 0)

    def _add(self, x, y):
        b = int(y // PROFILE_BAND)
        self.left[b] = min(self.left.get(b, x), x)
        self.right[b] = max(self.right.get(b, x), x)

    def _line(self, p0, p1, steps):
        for i in range(steps + 1):
            t = i / steps
            self._add(p0[0] + (p1[0] - p0[0]) * t, p0[1] + (p1[1] - p0[1]) * t)

    def _moveTo(self, p):
        self.cur = p

    def _lineTo(self, p):
        self._line(self.cur, p, max(2, int(abs(p[1] - self.cur[1]) / 4)))
        self.cur = p

    def _curveToOne(self, p1, p2, p3):
        p0 = prev = self.cur
        for i in range(1, 25):
            t = i / 24
            mt = 1 - t
            x = mt**3 * p0[0] + 3 * mt * mt * t * p1[0] + 3 * mt * t * t * p2[0] + t**3 * p3[0]
            y = mt**3 * p0[1] + 3 * mt * mt * t * p1[1] + 3 * mt * t * t * p2[1] + t**3 * p3[1]
            self._line(prev, (x, y), 2)
            prev = (x, y)
        self.cur = p3

    def _qCurveToOne(self, p1, p2):
        p0 = prev = self.cur
        for i in range(1, 17):
            t = i / 16
            mt = 1 - t
            x = mt * mt * p0[0] + 2 * mt * t * p1[0] + t * t * p2[0]
            y = mt * mt * p0[1] + 2 * mt * t * p1[1] + t * t * p2[1]
            self._line(prev, (x, y), 2)
            prev = (x, y)
        self.cur = p2


class _Shaper:
    """Shapes pairs with kerning and measures the gap between their outlines."""

    def __init__(self, path):
        tt = TTFont(path)
        self.gs, self.order = tt.getGlyphSet(), tt.getGlyphOrder()
        self.font = hb.Font(hb.Face(hb.Blob.from_file_path(path)))
        self.profiles = {}

    def _profile(self, gid):
        if gid not in self.profiles:
            self.profiles[gid] = ProfilePen(self.gs)
            self.gs[self.order[gid]].draw(self.profiles[gid])
        return self.profiles[gid]

    def gap(self, pair):
        """(gap, left glyph, right glyph), or None if the pair does not shape
        to two glyphs that share a height."""
        buf = hb.Buffer()
        buf.add_str(pair)
        buf.guess_segment_properties()
        hb.shape(self.font, buf, {'liga': False, 'kern': True})
        info, pos = buf.glyph_infos, buf.glyph_positions
        if len(info) != 2:
            return None
        left, right = self._profile(info[0].codepoint), self._profile(info[1].codepoint)
        gaps = [pos[0].x_advance + right.left[k] - left.right[k] for k in left.right if k in right.left]
        if not gaps:
            return None
        return min(gaps), self.order[info[0].codepoint], self.order[info[1].codepoint]


def find_collisions(path, min_gap=1):
    """(gap, pair, left glyph, right glyph) for every pair of CHARS closer
    than min_gap, closest first."""
    shaper = _Shaper(path)
    hits = []
    for a, b in itertools.product(CHARS, repeat=2):
        found = shaper.gap(a + b)
        if found and found[0] < min_gap:
            hits.append((round(found[0]), a + b, found[1], found[2]))
    return sorted(hits)


def open_collisions(font, path):
    """Saves font to path and adds a kerning lookup that opens every touching
    pair to CLEARANCE. Returns how many pairs it opened."""
    font.save(path)
    hits = find_collisions(path)
    if not hits:
        return 0
    pairs = {(a, b): (buildValue({'XAdvance': CLEARANCE - gap}), None) for gap, _, a, b in hits}
    gpos = font['GPOS'].table
    lookup = ot.Lookup()
    lookup.LookupType = 2
    lookup.LookupFlag = 0
    lookup.SubTable = buildPairPosGlyphs(pairs, font.getReverseGlyphMap())
    lookup.SubTableCount = len(lookup.SubTable)
    gpos.LookupList.Lookup.append(lookup)
    index = len(gpos.LookupList.Lookup) - 1
    gpos.LookupList.LookupCount = index + 1
    for rec in gpos.FeatureList.FeatureRecord:
        if rec.FeatureTag == 'kern':
            rec.Feature.LookupListIndex.append(index)
            rec.Feature.LookupCount += 1
    return len(pairs)


def match_open_gaps(font, path, base_of):
    """Saves font to path, then puts f and t as far from a following o as n
    is: the class spacing leaves the overhanging f too loose and the t too
    tight. base_of maps each glyph to its base letter. Returns the change."""
    font.save(path)
    shaper = _Shaper(path)
    target = shaper.gap('no')[0]
    deltas = {ch: round(target - shaper.gap(ch + 'o')[0]) for ch in 'ft'}
    hmtx = font['hmtx']
    for name, base in base_of.items():
        if base in deltas:
            hmtx[name] = (hmtx[name][0] + deltas[base], hmtx[name][1])
    return deltas


def settle_collisions(font, path, passes=4):
    """Opens touching pairs until none are left, or for at most passes rounds."""
    total = 0
    for _ in range(passes):
        opened = open_collisions(font, path)
        total += opened
        if not opened:
            break
    return total
