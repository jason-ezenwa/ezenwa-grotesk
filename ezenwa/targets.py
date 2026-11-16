"""Ezenwa Grotesk's targets, recorded once in targets.json.

They were measured from Founders Grotesk, the reference, as aggregates only:
heights, stems, and per-class mean widths and side bearings. Then they were
scaled: x-height to 470 at Regular, lowercase widths and spacing by 1.04,
capitals and figures by 640/630, and stems by 1.025.
"""
import json
import os

with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'targets.json')) as fh:
    _TARGETS = json.load(fh)


def targets(style, italic):
    return _TARGETS[f'{style}{" Italic" if italic else ""}']
