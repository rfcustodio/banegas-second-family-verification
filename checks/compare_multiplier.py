#!/usr/bin/env python3
"""Checks Table 10 and the percentages of Section IX-E (full multiplier and squaring at
degrees 163 and 571) from data/multiplier.json, written by verification/multiplier.py
(which builds the Karatsuba product and runs the greedy count of the squaring reductions).
Since v23 the table lists EVERY irreducible member of the two families at these degrees,
because the modulus with the smallest reduction bound need not have the cheapest squaring;
the squaring comparison is made separately, minimizing over the members of each family.
Standard library only.  Usage: python3 checks/compare_multiplier.py"""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
J = json.load(open(ROOT / 'data' / 'multiplier.json'))
ok = True
def expect(label, got, want):
    global ok
    good = got == want; ok &= good
    print(f"  {'ok ' if good else 'BAD'} {label}: {got}" + ('' if good else f'  (paper: {want})'))
K = {int(m): v for m, v in J['karatsuba'].items()}; R = J['rows']
expect('Karatsuba product m=163 (XOR, AND, correct)', tuple(K[163]), (12001, 6203, True))
expect('Karatsuba product m=571 (XOR, AND, correct)', tuple(K[571]), (90703, 47916, True))
# paper: reduction, schoolbook, Karatsuba, squaring (lexicographic greedy); the fifth value of
# each row of the JSON is the best of 20 randomized greedy runs, quoted in the text.
T10 = {'163 second (71,46)': (440, 26684, 12441, 173), '163 first (74,15)': (487, 26731, 12488, 199),
       '163 first (63,37)': (487, 26731, 12488, 162), '163 NIST': (571, 26815, 12572, 246),
       '571 second (207,182)': (1528, 326428, 92231, 649), '571 second (359,106)': (1604, 326504, 92307, 570),
       '571 second (527,22)': (1534, 326434, 92237, 570), '571 first (218,135)': (1711, 326611, 92414, 679),
       '571 NIST': (2003, 326903, 92706, 861)}
expect('rows of Table 10', sorted(R), sorted(T10))
for k, want in T10.items():
    red, sch, kar, sq, sqr = R[k]
    m = int(k.split()[0])
    expect(f'Table 10, {k}', (red, sch, kar, sq), want)
    expect('  consistency: schoolbook = (m-1)^2 + reduction, Karatsuba = product + reduction', (sch - red, kar - red), ((m - 1) ** 2, K[m][0]))
# the table lists exactly the irreducible members of the census
def members(fn, m): return {tuple(map(int, l.split()))[1:] for l in open(ROOT / 'data' / fn) if l.split() and int(l.split()[0]) == m}
for m in (163, 571):
    for fam, fn in (('second', 'fam2_irr.txt'), ('first', 'fam1_irr.txt')):
        got = {tuple(map(int, k.split('(')[1].rstrip(')').split(','))) for k in R if k.startswith(f'{m} {fam}')}
        expect(f'm={m}: {fam}-family rows = irreducible members in data/{fn}', sorted(got), sorted(members(fn, m)))
def best(m, fam, col): return min(v[col] for k, v in R.items() if k.startswith(f'{m} {fam}'))
pct = lambda a, b: round(100 * (a - b) / a, 1)
s = {(m, f): best(m, f, 3) for m in (163, 571) for f in ('second', 'first', 'NIST')}
expect('squaring, minimized in each family, m=163 (second, first, NIST)', (s[163, 'second'], s[163, 'first'], s[163, 'NIST']), (173, 162, 246))
expect('squaring, minimized in each family, m=571 (second, first, NIST)', (s[571, 'second'], s[571, 'first'], s[571, 'NIST']), (570, 679, 861))
expect('m=163: second family needs more gates than the first (%)', round(100 * (s[163, 'second'] - s[163, 'first']) / s[163, 'first'], 1), 6.8)
expect('m=163: squaring savings vs NIST, second / first (%)', (pct(s[163, 'NIST'], s[163, 'second']), pct(s[163, 'NIST'], s[163, 'first'])), (29.7, 34.1))
expect('m=571: squaring savings of the second family vs first / NIST (%)', (pct(s[571, 'first'], s[571, 'second']), pct(s[571, 'NIST'], s[571, 'second'])), (16.1, 33.8))
expect('m=571: squaring of the member with the smallest reduction bound, f_{207,182}', R['571 second (207,182)'][3], 649)
changed = {k: v[4] for k, v in R.items() if v[4] != v[3]}
expect('20 randomized greedy runs change only the member with c=106, to 549', changed, {'571 second (359,106)': 549})
r = lambda m: (best(m, 'second', 2), best(m, 'NIST', 2))
expect('Karatsuba multiplier saving vs NIST at 163 / 571 (%)', tuple(round(100 * (r(m)[1] - r(m)[0]) / r(m)[1], 2) for m in (163, 571)), (1.04, 0.51))
print('\nALL OK' if ok else '\nSOME VALUES DIFFER')
sys.exit(0 if ok else 1)
