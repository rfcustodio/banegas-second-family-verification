#!/usr/bin/env python3
"""Recomputes Table 7 and the numbers of Section IX-C (comparison with type I, type II and
general pentanomials over the 502 degrees 5 <= m <= 1100 without irreducible trinomials)
from the census files in data/. Type II costs are greedy counts, read from
data/other_families.json (written by verification/other_families.py, which runs the
greedy algorithm). Standard library only.  Usage: python3 checks/compare_other_families.py"""
import json, math, statistics as st, sys
from pathlib import Path
D = Path(__file__).resolve().parent.parent / 'data'
def load(fn):
    out = {}
    for l in open(D / fn):
        a = list(map(int, l.split())); out.setdefault(a[0], []).append(a[1:])
    return out
tri = {int(l.split()[0]) for l in open(D / 'tri.txt') if int(l.split()[1]) > 0}
noT = [m for m in range(5, 1101) if m not in tri]
sec, fst = load('fam2_irr.txt'), load('fam1_irr.txt')
t1, t2, esp, pmin = load('type1_irr.txt'), load('type2_irr.txt'), load('rmh_class2_irr.txt'), load('pent_min.txt')
gr = json.load(open(D / 'other_families.json'))['typeII']
SPEC = {(2, 1): (6, 7), (3, 1): (10, 12), (4, 1): (14, 15), (5, 1): (16, 18), (3, 2): (16, 18)}
N = lambda b, c: c * ((b + c) // (3 * c)) + max(0, (b + c) % (3 * c) - 2 * c)
def c2(m, b, c):
    g = math.gcd(b, c); v = min(3 * m - c - 3, 3 * m - 3 - N(b, c))
    if (b // g, c // g) in SPEC: R2, R1 = SPEC[(b // g, c // g)]; v = min(v, (g - 1) * R1 + R2)
    return v
C = {'second': {m: min(c2(m, b, c) for b, c in sec[m]) for m in noT if m in sec},
     'first': {m: min(12 * m // 5 - 1 if b == 2 * c else 3 * m - 2 for b, c in fst[m]) for m in noT if m in fst},
     'type I': {m: 3 * m - 2 for m in noT if m in t1},
     'type II': {m: gr[str(m)] for m in noT if m in t2},
     'k3 <= m/2': {m: 4 * (m - 1) for m in noT if m in pmin and pmin[m][0][0] > 0}}
ok = True
def expect(label, got, want):
    global ok
    good = got == want; ok &= good
    print(f"  {'ok ' if good else 'BAD'} {label}: {got}" + ('' if good else f'  (paper: {want})'))
S = C['second']
print('Table 7 (degrees, XORs per bit, shared degrees, second cheaper, mean saving %)')
paper = {'second': (288, 2.70), 'first': (229, 2.99, 176, 176, 9.7), 'type I': (361, 2.99, 204, 204, 9.5),
         'type II': (318, 3.73, 183, 183, 27.0), 'k3 <= m/2': (502, 3.98, 288, 288, 32.1)}
for f, Df in C.items():
    row = (len(Df), round(st.mean(Df[m] / m for m in Df), 2))
    if f != 'second':
        sh = [m for m in Df if m in S]
        row += (len(sh), sum(S[m] < Df[m] for m in sh), round(100 * st.mean((Df[m] - S[m]) / Df[m] for m in sh), 1))
    expect(f, row, paper[f])
best = {m: min(C[f][m] for f in C if f != 'second' and m in C[f]) for m in S}
rel = [(best[m] - S[m]) / best[m] for m in S]
expect('second cheaper than every other family (degrees; min, max, mean %)',
       (sum(r > 0 for r in rel), round(100 * min(rel), 1), round(100 * max(rel), 1), round(100 * st.mean(rel), 1)), (288, 5.6, 33.2, 11.7))
fam4 = ('second', 'first', 'type I', 'type II')
expect('degrees covered by the four families; by the second family only',
       (sum(any(m in C[f] for f in fam4) for m in noT), sorted(m for m in S if not any(m in C[f] for f in fam4[1:]))[:2],
        sum(1 for m in S if not any(m in C[f] for f in fam4[1:]))), (484, [69, 306], 15))
expect('class x^m+x^(m-s)+x^(m-2s)+x^(m-3s)+1 in degrees without trinomials', sum(m in esp for m in noT), 0)
expect('NIST degrees: type I 163, 283; type II 163, 283, 571',
       (C['type I'].get(163), C['type I'].get(283), C['type II'][163], C['type II'][283], C['type II'][571]), (487, 847, 665, 1021, 2149))
print('\nALL OK' if ok else '\nSOME VALUES DIFFER')
sys.exit(0 if ok else 1)
