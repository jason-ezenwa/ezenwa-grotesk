#!/usr/bin/env python3
"""Reports every common character pair whose outlines touch.

Usage: python3 check.py fonts/EzenwaGrotesk-Regular.ttf [min-gap]
"""
import sys

from ezenwa.collisions import find_collisions

if __name__ == '__main__':
    path, min_gap = sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 1
    hits = find_collisions(path, min_gap)
    print(f'{path}: {len(hits)} pairs closer than {min_gap} units')
    print(' '.join(f'{pair}:{gap}' for gap, pair, _, _ in hits[:80]))
