"""Design constants, in a 1000-unit em. Measured targets are in targets.json."""

STYLES = [('Light', 300), ('Regular', 400), ('Medium', 500), ('Semibold', 600), ('Bold', 700)]

# Proportions
CAP = 640                # cap height that sets the overall scale
ROUNDNESS = 0.5          # how far the o's fullness moves from Archivo's toward the target

# Fitting limits
MAX_STRETCH = 0.03       # no glyph is stretched or squeezed by more than this
OVERSHOOT_BAND = 30      # overshoot zone kept at the x-height scale
CORNER = 28              # rounded corners with a shorter chord become sharp
CLEARANCE = 12           # gap opened between touching pairs

# Letters, as shares of the o's width or of the letter's own stem
F_JOIN = 0.05            # f: the stem starts curving this far from x-height to the top
F_REACH = 0.5            # f: the hook reaches this many stems past the crossbar
F_MIN_WIDTH = 0.59       # f: the hook spans at least this share of the o
F_TERMINAL = 0.45        # f: the hook is cut this far from the join to the top
F_DEPTH = 0.24           # f: the hook is cut at least this far down into its counter
T_JOIN = 0.28            # t: the stem starts curving this far up the x-height
T_REACH = 0.25           # t: the foot reaches this many stems past the crossbar
T_MIN_WIDTH = 0.53       # t: the foot spans at least this share of the o
T_TERMINAL = 0.3         # t: the foot is cut this far from the join to the bottom
T_DEPTH = 0.42           # t: the foot is cut at least this far up into its counter
MIN_COUNTER = 0.4        # f and t: the hook's counter is at least this many stems wide and tall

# Glyph groups
LC = 'abcdefghijklmnopqrstuvwxyz'
UC = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
FIG = '0123456789'
GROUPS = {'lc': LC, 'uc': UC, 'fig': FIG}
SUBCLASS = {
    'lc-straight': 'hijlmnru', 'lc-round': 'abcdegopqs', 'lc-diagonal': 'kvwxyz', 'lc-open': 'ft',
    'uc-straight': 'BDEFHIJKLMNPRU', 'uc-round': 'CGOQS', 'uc-diagonal': 'AVWXYZ', 'uc-open': 'T',
    'figures': FIG,
}
CLASS_OF = {ch: cls for cls, chars in SUBCLASS.items() for ch in chars}
DIGIT_NAMES = {'zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine'}
MATH_SIGNS = ['plus', 'minus', 'multiply', 'divide', 'equal', 'less', 'greater',
              'plusminus', 'notequal', 'lessequal', 'greaterequal', 'approxequal', 'equivalence']

# File metrics
LINE_ASCENT, LINE_DESCENT = 960, -220
WIN_ASCENT, WIN_DESCENT = 1100, 420   # one clipping box for the whole family

# Names
VERSION = '1.000'
DESIGNER = 'Chukwuemelie Ezenwa'
COPYRIGHT = ('Copyright 2020 The Archivo Project Authors '
             '(https://github.com/Omnibus-Type/Archivo). '
             'Copyright 2026 Chukwuemelie Ezenwa.')
LICENSE = ('This Font Software is licensed under the SIL Open Font License, Version 1.1. '
           'This license is available with a FAQ at: https://openfontlicense.org')
LICENSE_URL = 'https://openfontlicense.org'
