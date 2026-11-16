"""Sorts glyphs into case groups and spacing subclasses."""
import unicodedata

from .spec import CLASS_OF, DIGIT_NAMES


def _reverse_cmap(font):
    """Glyph name to the first character it draws."""
    rev = {}
    for cp, name in font.getBestCmap().items():
        rev.setdefault(name, cp)
    return rev


def _codepoint(name, rev):
    """The character a glyph draws, from the cmap or from its name."""
    if name in rev:
        return rev[name]
    stem = name.split('.')[0].split('_')[0]
    if stem.startswith('uni') and len(stem) >= 7:
        try:
            return int(stem[3:7], 16)
        except ValueError:
            return None
    if len(stem) == 1:
        return ord(stem)
    return rev.get(stem)


def glyph_classes(font):
    """Maps each glyph to a case ('lc', 'uc' or 'other') and a spacing
    subclass (or None)."""
    rev = _reverse_cmap(font)
    glyf, order = font['glyf'], font.getGlyphOrder()
    case, sub = {}, {}
    for name in order:
        cp = _codepoint(name, rev)
        cat = unicodedata.category(chr(cp)) if cp is not None else ''
        if '.case' in name:
            case[name] = 'other'
        elif cat in ('Ll', 'Mn') or name.endswith('comb'):
            case[name] = 'lc'
        elif cat == 'Lu':
            case[name] = 'uc'
        else:
            case[name] = 'other'

        sub[name] = None
        if cp is not None and '.tf' not in name and '.tosf' not in name:
            base = unicodedata.normalize('NFD', chr(cp))[0]
            sub[name] = CLASS_OF.get(base) or CLASS_OF.get(name.split('.')[0])

    # Composites inherit the case of their base component.
    for name in order:
        gl = glyf[name]
        if gl.isComposite() and case[name] == 'other':
            case[name] = case.get(gl.components[0].glyphName, 'other')
    return case, sub


def figure_variants(font):
    """Alternate figures (tabular, oldstyle, numerators, slashed and so on) and
    the superscript, subscript and fraction characters."""
    rev = {n: cp for cp, n in font.getBestCmap().items()}
    out = set()
    for name in font.getGlyphOrder():
        if '.' in name and name.split('.')[0] in DIGIT_NAMES:
            out.add(name)
        elif name in rev and unicodedata.category(chr(rev[name])) == 'No':
            out.add(name)
    return out


def base_letters(font):
    """Maps each glyph to the letter its character is built on, if any."""
    rev = _reverse_cmap(font)
    out = {}
    for name in font.getGlyphOrder():
        cp = _codepoint(name, rev)
        if cp is not None:
            out[name] = unicodedata.normalize('NFD', chr(cp))[0]
    return out
