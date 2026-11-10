#!/usr/bin/env python3
"""Checks Table 10 and the percentages of Section IX-D (full multiplier and squaring at
degrees 163 and 571) from data/multiplier.json, written by verification/multiplier.py
(which builds the Karatsuba product and runs the greedy count of the squaring reductions).
Standard library only.  Usage: python3 checks/compare_multiplier.py"""
import json, sys
from pathlib import Path
J = json.load(open(Path(__file__).resolve().parent.parent / 'data' / 'multiplier.json'))
ok = True
def expect(label, got, want):
    global ok
    good = got == want; ok &= good
    print(f"  {'ok ' if good else 'BAD'} {label}: {got}" + ('' if good else f'  (paper: {want})'))
K = {int(m): v for m, v in J['karatsuba'].items()}; R = J['rows']
expect('Karatsuba product m=163 (XOR, AND, correct)', tuple(K[163]), (12001, 6203, True))
expect('Karatsuba product m=571 (XOR, AND, correct)', tuple(K[571]), (90703, 47916, True))
T10 = {'163 second': (440, 26684, 12441, 173), '163 first': (487, 26731, 12488, 199), '163 NIST': (571, 26815, 12572, 246),
       '571 second': (1528, 326428, 92231, 649), '571 first': (1711, 326611, 92414, 679), '571 NIST': (2003, 326903, 92706, 861)}
for k, want in T10.items():
    red, sch, kar, sq = R[k]
    m = int(k.split()[0])
    expect(f'Table 10, {k}', (red, sch, kar, sq), want)
    expect(f'  consistency: schoolbook = (m-1)^2 + reduction, Karatsuba = product + reduction', (sch - red, kar - red), ((m - 1) ** 2, K[m][0]))
pct = lambda a, b: round(100 * (a - b) / a, 1)
expect('squaring savings vs first family at 163 / 571 (%)', (pct(R['163 first'][3], R['163 second'][3]), pct(R['571 first'][3], R['571 second'][3])), (13.1, 4.4))
expect('squaring savings vs NIST at 163 / 571 (%)', (pct(R['163 NIST'][3], R['163 second'][3]), pct(R['571 NIST'][3], R['571 second'][3])), (29.7, 24.6))
expect('Karatsuba multiplier saving vs NIST at 163, about 1%', pct(R['163 NIST'][2], R['163 second'][2]), 1.0)
print('\nALL OK' if ok else '\nSOME VALUES DIFFER')
sys.exit(0 if ok else 1)
