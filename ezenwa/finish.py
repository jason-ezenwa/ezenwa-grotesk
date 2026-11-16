"""File-level details: names, line metrics, math widths, dropout control,
style table, and unreachable glyphs removed."""
from fontTools import subset
from fontTools.otlLib.builder import buildStatTable
from fontTools.ttLib import newTable
from fontTools.ttLib.tables import ttProgram

from .spec import (COPYRIGHT, DESIGNER, LICENSE, LICENSE_URL, LINE_ASCENT, LINE_DESCENT,
                   MATH_SIGNS, VERSION, WIN_ASCENT, WIN_DESCENT)

DROPOUT_CONTROL = b'\xb8\x01\xff\x85\xb0\x04\x8d'


def style_name(style, italic):
    if not italic:
        return style
    return 'Italic' if style == 'Regular' else f'{style} Italic'


def postscript_name(style, italic):
    return 'EzenwaGrotesk-' + style_name(style, italic).replace(' ', '')


def set_names(font, style, weight, italic):
    sub = style_name(style, italic)
    ps = postscript_name(style, italic)
    ribbi = style in ('Regular', 'Bold')
    legacy_sub = ' '.join(w for w in ('Bold' if style == 'Bold' else '', 'Italic' if italic else '') if w)
    names = {
        0: COPYRIGHT,
        1: 'Ezenwa Grotesk' if ribbi else f'Ezenwa Grotesk {style}',
        2: legacy_sub or 'Regular',
        3: f'{VERSION};{ps}',
        4: f'Ezenwa Grotesk {sub}',
        5: f'Version {VERSION}',
        6: ps,
        8: DESIGNER,
        9: f'{DESIGNER}; Archivo by Omnibus-Type',
        13: LICENSE,
        14: LICENSE_URL,
        16: 'Ezenwa Grotesk',
        17: sub,
    }
    table = font['name']
    table.names = []
    for name_id, value in names.items():
        table.setName(value, name_id, 3, 1, 0x409)

    os2 = font['OS/2']
    os2.usWeightClass = weight
    os2.achVendID = 'EZNW'
    sel = os2.fsSelection & ~0b1100001
    if italic:
        sel |= 1 << 0
    if style == 'Bold':
        sel |= 1 << 5
    if not italic and style != 'Bold':
        sel |= 1 << 6
    os2.fsSelection = sel | (1 << 8)
    font['head'].macStyle = (1 if style == 'Bold' else 0) | (2 if italic else 0)


def _center_in(font, name, width):
    glyf, hmtx = font['glyf'], font['hmtx']
    gl, adv = glyf[name], hmtx[name][0]
    if adv == width:
        return
    dx = (width - adv) // 2
    if gl.isComposite():
        for c in gl.components:
            c.x += dx
    elif gl.numberOfContours > 0:
        gl.coordinates.translate((dx, 0))
    gl.recalcBounds(glyf)
    hmtx[name] = (width, getattr(gl, 'xMin', 0))


def _drop_unreachable(font, cmap):
    opts = subset.Options()
    opts.layout_features = ['*']
    opts.name_IDs = ['*']
    opts.name_languages = ['*']
    opts.glyph_names = True
    opts.notdef_outline = True
    opts.legacy_kern = True
    opts.hinting = True
    sub = subset.Subsetter(opts)
    sub.populate(unicodes=list(cmap))
    sub.subset(font)


def _stat(font, style, weight, italic):
    """Each static file describes only its own place in the family."""
    regular = {'flags': 0x2} if weight == 400 else {}
    roman = {'value': 0, 'name': 'Roman', 'flags': 0x2, 'linkedValue': 1}
    buildStatTable(font, [
        {'tag': 'wght', 'name': 'Weight', 'values': [{'value': weight, 'name': style, **regular}]},
        {'tag': 'ital', 'name': 'Italic', 'values': [{'value': 1, 'name': 'Italic'} if italic else roman]},
    ], locations=None, elidedFallbackName=2)


def finish(font, style, weight, italic):
    hmtx, cmap = font['hmtx'], font.getBestCmap()
    if 0xA0 in cmap:
        hmtx[cmap[0xA0]] = (hmtx[cmap[0x20]][0], 0)

    # Math signs share the tabular figures' width so sums line up.
    signs = [n for n in MATH_SIGNS if n in hmtx.metrics]
    width = hmtx['zero.tf'][0] if 'zero.tf' in hmtx.metrics else max(hmtx[n][0] for n in signs)
    for n in signs:
        _center_in(font, n, width)

    prep = newTable('prep')
    prep.program = ttProgram.Program()
    prep.program.fromBytecode(DROPOUT_CONTROL)
    font['prep'] = prep

    _drop_unreachable(font, cmap)

    glyf = font['glyf']
    y_max = max(getattr(glyf[n], 'yMax', 0) for n in font.getGlyphOrder())
    y_min = min(getattr(glyf[n], 'yMin', 0) for n in font.getGlyphOrder())
    assert y_max <= WIN_ASCENT and -y_min <= WIN_DESCENT, (y_max, y_min)

    os2, hhea = font['OS/2'], font['hhea']
    hhea.ascent, hhea.descent, hhea.lineGap = LINE_ASCENT, LINE_DESCENT, 0
    os2.sTypoAscender, os2.sTypoDescender, os2.sTypoLineGap = LINE_ASCENT, LINE_DESCENT, 0
    os2.fsSelection |= 1 << 7
    os2.usWinAscent, os2.usWinDescent = WIN_ASCENT, WIN_DESCENT
    os2.recalcAvgCharWidth(font)
    font['head'].fontRevision = float(VERSION)

    _stat(font, style, weight, italic)
    font['name'].names = [r for r in font['name'].names if r.platformID != 1]
