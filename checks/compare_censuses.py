#!/usr/bin/env python3
"""Cross-checks the two independent irreducibility censuses for 5 <= m <= 1100 and
recomputes Table 6 and the numbers of Section IX from the authors' census.

  authors' census     : data/fam2_irr.txt, data/fam1_irr.txt, data/tri.txt
                        (produced by generator/xorred.c, word-level Rabin test in C)
  independent census  : independent/censo_table3_dados.json
                        (produced by independent/censo_table3.py, pure Python)

The two censuses were written separately, in different languages; agreement on every
(m, b, c) is strong evidence that the irreducibility lists behind Table 6 are right.
Usage: python3 checks/compare_censuses.py
"""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent

def load_txt(fn):
    S = {}
    for l in open(ROOT / 'data' / fn):
        m, b, c = map(int, l.split()); S.setdefault(m, set()).add((b, c))
    return S

F2, F1 = load_txt('fam2_irr.txt'), load_txt('fam1_irr.txt')
T = {int(l.split()[0]) for l in open(ROOT / 'data' / 'tri.txt') if int(l.split()[0]) >= 5}  # file starts at m=2
J = json.load(open(ROOT / 'independent' / 'censo_table3_dados.json'))
J2 = {int(m): {tuple(x) for x in v} for m, v in J['segunda'].items() if v}
J1 = {int(m): {tuple(x) for x in v} for m, v in J['primeira'].items() if v}
JT = {int(m) for m, v in J['trinomio'].items() if v}

ok = True
for name, A, B in (('second family', F2, J2), ('first family', F1, J1)):
    same = A == B; ok &= same
    diff = sorted(set(A) ^ set(B))[:5]
    print(f"{name}: authors {sum(map(len, A.values()))} members in {len(A)} degrees, "
          f"independent {sum(map(len, B.values()))} in {len(B)} degrees -> {'IDENTICAL' if same else 'DIFFERENT ' + str(diff)}")
same = T == JT; ok &= same
print(f"trinomials: authors {len(T)} degrees, independent {len(JT)} -> {'IDENTICAL' if same else 'DIFFERENT'}")

# ---- Table 6 from the authors' census
# Second family: generic members cost min(3m-c-3, 3m-3-N(b,c)) (Theorems 8 and 13); special
# members cost the strip bound (2) with the optimal values of Table 2. First family: 3m-2,
# or 12m/5-1 when b = 2c.
from math import gcd
BASE = {(2, 1): (6, 7), (3, 1): (10, 12), (4, 1): (14, 15), (5, 1): (16, 18), (3, 2): (16, 18)}
def N(b, c): return c * ((b + c) // (3 * c)) + max(0, (b + c) % (3 * c) - 2 * c)
def special(b, c):
    g = gcd(b, c); return (b // g, c // g) in BASE
def cost2(m, b, c, chain=True):
    g = gcd(b, c); base = (b // g, c // g)
    best = 3 * m - c - 3
    if chain: best = min(best, 3 * m - 3 - N(b, c))
    if base in BASE: R2, R1 = BASE[base]; best = min(best, (g - 1) * R1 + R2)
    return best
def c2(m, chain=True): return min(cost2(m, b, c, chain) for b, c in F2[m])
def c1(m): return min(12 * m // 5 - 1 if b == 2 * c else 3 * m - 2 for b, c in F1[m])
both = set(F2) & set(F1)
cheaper2 = [m for m in both if c2(m) < c1(m)]
cheaper2_alg1 = [m for m in both if c2(m, False) < c1(m)]
noT = [m for m in range(5, 1101) if m not in T]
gen = [m for m in F2 if any(not special(b, c) for b, c in F2[m])]
def best_gen(m, chain=True):
    return min(min(3 * m - c - 3, 3 * m - 3 - N(b, c)) if chain else 3 * m - c - 3
               for b, c in F2[m] if not special(b, c))
improved = [m for m in F2 if c2(m) < c2(m, False)]
pct = lambda L, f: round(100 * sum((c1(m) - f(m)) / c1(m) for m in L) / len(L), 1)
print('\nTable 6 (authors\' census):')
rows = [
    ('irreducible members of the second family', sum(map(len, F2.values())), 1508),
    ('degrees with members, second family', len(F2), 720),
    ('degrees with members, first family', len(F1), 502),
    ('degrees with members of both families', len(both), 405),
    ('  second family cheaper', len(cheaper2), 405),
    ('  mean saving (%)', pct(cheaper2, c2), 9.7),
    ('  mean saving with Theorem 8 alone (%)', pct(cheaper2_alg1, lambda m: c2(m, False)), 7.3),
    ('degrees in which Theorem 13 improves the best member', len(improved), 379),
    ('  of them without irreducible trinomials', sum(m not in T for m in improved), 160),
    ('degrees without irreducible trinomials', len(noT), 502),
    ('  covered by second family', sum(m in F2 for m in noT), 288),
    ('  covered by first family', sum(m in F1 for m in noT), 229),
    ('  covered by second family only', sum(m in F2 and m not in F1 for m in noT), 112),
    ('  covered by neither', sum(m not in F2 and m not in F1 for m in noT), 161),
    ('mean cost per bit, best generic second-family member', round(sum(best_gen(m) / m for m in gen) / len(gen), 2), 2.70),
    ('  the same with Theorem 8 only', round(sum(best_gen(m, False) / m for m in gen) / len(gen), 2), 2.77),
]
for label, got, want in rows:
    good = got == want; ok &= good
    print(f"  {'ok ' if good else 'BAD'} {label}: {got}" + ('' if good else f' (paper: {want})'))
rel = max((c2(m, False) - c2(m)) / c2(m, False) for m in improved)
m975 = (c2(975, False), c2(975))
good = round(100 * rel, 1) == 11.1 and m975 == (2921, 2598); ok &= good
print(f"  {'ok ' if good else 'BAD'} largest improvement by Theorem 13: {round(100 * rel, 1)}%; m=975: {m975[0]} -> {m975[1]} (paper: 11.1%, 2921 -> 2598)")
good = (c2(5), c1(5), c2(155), c1(155), best_gen(155)) == (10, 11, 370, 371, 411); ok &= good
print(f"  {'ok ' if good else 'BAD'} special members at m=5 and m=155: (10 vs 11), (370 vs 371; best generic 411)")
print('\nALL OK' if ok else '\nSOME VALUES DIFFER')
sys.exit(0 if ok else 1)
