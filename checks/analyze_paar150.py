#!/usr/bin/env python3
"""Recomputes every number of Observation 12 and Figure 2 from the raw greedy data
data/paar150.txt (produced by generator/xorred.c, see data/README.md).

Columns of data/paar150.txt:  m  a  b  c  dXOR  CX  depth(CX)  RG  depth(RG)
  CX = Conta-XOR count (lexicographic tie-breaking), RG = best of CX and 20 greedy runs
  with random tie-breaking.  a = b + c.
Usage: python3 checks/analyze_paar150.py
"""
from pathlib import Path
from fractions import Fraction
R = [list(map(int, l.split())) for l in open(Path(__file__).resolve().parent.parent / 'data' / 'paar150.txt')]
special = lambda b, c: Fraction(b, c) in (Fraction(3, 2), 2, 3, 4, 5)
G = [r for r in R if not special(r[2], r[3])]
cf = lambda m, c: 3 * m - c - 3
print(f'pairs with 5<=m<=150: {len(R)}  (paper: 3674);  generic: {len(G)}  (paper: 3541)')
a = all(min(r[5], r[7]) >= cf(r[0], r[3]) for r in G)
print(f'(a) closed form never longer than CX or RG on generic members: {a}')
lt = [r for r in G if r[2] < 2 * r[3]]
print(f'(b) b<2c: {len(lt)} members (paper: 879); CX == 2m+3c-3 for all: {all(r[5] == 2*r[0]+3*r[3]-3 for r in lt)}; '
      f'gain == 2c-b for all: {all(r[5]-cf(r[0],r[3]) == 2*r[3]-r[2] for r in lt)}')
mid = [r for r in G if 2 * r[3] < r[2] < 6 * r[3]]
print(f'(c) 2c<b<6c: {len(mid)} members (paper: 1312); CX == 3m-c-3 for all: {all(r[5] == cf(r[0], r[3]) for r in mid)}')
big = [r for r in G if r[2] >= 6 * r[3]]
worse = [r for r in big if r[5] > cf(r[0], r[3])]
print(f'(d) b>=6c: {len(big)} members (paper: 1350); CX worse in {len(worse)} (paper: 392), '
      f'max excess {max(r[5]-cf(r[0],r[3]) for r in worse)} (paper: 112)')
imp = [r for r in G if r[7] < r[5]]
print(f'random tie-breaking improved CX in {len(imp)} generic members (all with b>=6c: {all(r[2] >= 6*r[3] for r in imp)}, '
      f'by at most {max(r[5]-r[7] for r in imp)}), and reached 3m-c-3 in {sum(1 for r in imp if r[7] == cf(r[0], r[3]))} of them '
      f'(corrected text: 212 / 12 / 1; the first version said "changed the outcome in only one case")')
S = [r for r in R if special(r[2], r[3])]
print(f'special members: {len(S)}; greedy shorter than 3m-c-3 in {sum(1 for r in S if min(r[5], r[7]) < cf(r[0], r[3]))}')
b3 = [r for r in S if r[2] == 3 * r[3]]
print(f'b=3c: CX == 12m/5-2 for all {len(b3)}: {all(5*(r[5]+2) == 12*r[0] for r in b3)}')
