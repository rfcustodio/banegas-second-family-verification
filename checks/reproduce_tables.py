#!/usr/bin/env python3
"""Recomputes Table 2 and Table 4 of the paper, and the numbers quoted in the abstract
and in Section 8, using the authors' generator (generator/fam2.py), the Conta-XOR
implementation (generator/contaxor.py) and the census lists in data/.
Usage: python3 checks/reproduce_tables.py      (about 1 minute)
"""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'generator'))
from fam2 import program, check
from contaxor import irredutivel, matriz_reducao, conta_xor

def poly(*e):
    p = 0
    for x in e: p ^= 1 << x
    return p

ok_all = True
def expect(label, got, want):
    global ok_all
    good = got == want; ok_all &= good
    print(f"  {'ok ' if good else 'BAD'} {label}: {got}" + ('' if good else f'  (paper: {want})'))

print('Table 2 (members of the second family at the NIST degrees)')
T2 = [  # m, b, c, dXOR, CX, 3m-c-3, depth   (values printed in the paper)
    (163, 71, 46, 649, 461, 440, 4), (233, 83, 75, 866, 688, 621, 4), (233, 201, 16, 1687, 680, 680, 7),
    (409, 179, 115, 1642, 1160, 1109, 4), (409, 265, 72, 1823, 1152, 1152, 4),
    (571, 207, 182, 2145, 1685, 1528, 4), (571, 359, 106, 2531, 1604, 1604, 4), (571, 527, 22, 6297, 1688, 1688, 11)]
for m, b, c, dx, cx, cf, dp in T2:
    f = poly(m, b + c, b, c, 0)
    L, n = matriz_reducao(f)
    P, out = program(b, c)
    print(f' f = x^{m}+x^{b+c}+x^{b}+x^{c}+1')
    expect('irreducible', irredutivel(f), True)
    expect('dXOR', sum(len(r) - 1 for r in L), dx)
    expect('Conta-XOR', conta_xor(L, n)[0], cx)
    expect('Algorithm 1 gates (correct)', (len(P.gates), check(b, c, P, out)), (cf, True))
    expect('Algorithm 1 depth', max(P.depth[o] for o in out), dp)

print('\nTable 4 (best known costs at the NIST degrees)')
nist = {163: (7, 6, 3, 571), 283: (12, 7, 5, 862), 571: (10, 5, 2, 2003)}
for m, (a, b, c, v) in nist.items():
    f = poly(m, a, b, c, 0); L, n = matriz_reducao(f)
    expect(f'NIST m={m}: irreducible, Conta-XOR', (irredutivel(f), conta_xor(L, n)[0]), (True, v))
for m, k in ((233, 74), (409, 87)):
    expect(f'NIST trinomial x^{m}+x^{k}+1 irreducible (cost 2m-2={2*m-2})', irredutivel(poly(m, k, 0)), True)
def best_members(fn, m):
    return [tuple(map(int, l.split()))[1:] for l in open(ROOT / 'data' / fn) if int(l.split()[0]) == m]
for m, want1, want2 in ((163, 487, 440), (233, 697, 621), (283, 847, None), (409, None, 1109), (571, 1711, 1528)):
    F1 = best_members('fam1_irr.txt', m); F2 = best_members('fam2_irr.txt', m)
    c1 = min((12 * m // 5 - 1 if b == 2 * c else 3 * m - 2) for b, c in F1) if F1 else None
    c2 = min(3 * m - c - 3 for b, c in F2) if F2 else None
    expect(f'm={m}: best first-family / second-family cost', (c1, c2), (want1, want2))
print('\nSection 8 (text)')
F2all = [tuple(map(int, l.split())) for l in open(ROOT / 'data' / 'fam2_irr.txt')]
expect('degrees = 0 mod 8 with a second-family member', len({m for m, b, c in F2all if m % 8 == 0}), 25)
for m, b, c, cost in ((48, 18, 15, 126), (144, 54, 45, 384)):
    P, out = program(b, c)
    expect(f'x^{m}+x^{b+c}+x^{b}+x^{c}+1: irreducible, gates', (irredutivel(poly(m, b + c, b, c, 0)), len(P.gates), check(b, c, P, out)), (True, cost, True))
pct = lambda new, old: round(100 * (old - new) / old, 1)
expect('savings vs NIST at 163 / 571 (%)', (pct(440, 571), pct(1528, 2003)), (22.9, 23.7))
expect('savings vs first family at 163 / 571 (%)', (pct(440, 487), pct(1528, 1711)), (9.7, 10.7))
expect('m=155: first family (b=2c) 12m/5-1 vs best second', (12 * 155 // 5 - 1, min(3 * 155 - c - 3 for m, b, c in F2all if m == 155)), (371, 411))
print('\nALL OK' if ok_all else '\nSOME VALUES DIFFER')
sys.exit(0 if ok_all else 1)
