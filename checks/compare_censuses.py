#!/usr/bin/env python3
"""Cross-checks the two independent irreducibility censuses for 5 <= m <= 1100 and
recomputes Table 3 from the authors' census.

  authors' census     : data/fam2_irr.txt, data/fam1_irr.txt, data/tri.txt
                        (produced by generator/xorred.c, word-level Rabin test in C)
  independent census  : independent/censo_table3_dados.json
                        (produced by independent/censo_table3.py, pure Python)

The two censuses were written separately, in different languages; agreement on every
(m, b, c) is strong evidence that the irreducibility lists behind Table 3 are right.
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

# ---- Table 3 from the authors' census
def c2(m): return min(7 * m // 4 - 1 if b == 2 * c else 3 * m - c - 3 for b, c in F2[m])
def c1(m): return min(12 * m // 5 - 1 if b == 2 * c else 3 * m - 2 for b, c in F1[m])
both = set(F2) & set(F1)
cheaper2 = [m for m in both if c2(m) < c1(m)]
noT = [m for m in range(5, 1101) if m not in T]
gen = [m for m in F2 if any(b != 2 * c for b, c in F2[m])]
best_gen = lambda m: min(3 * m - c - 3 for b, c in F2[m] if b != 2 * c)
print('\nTable 3 (authors\' census):')
rows = [
    ('irreducible members of the second family', sum(map(len, F2.values())), 1508),
    ('degrees with members, second family', len(F2), 720),
    ('degrees with members, first family', len(F1), 502),
    ('degrees with members of both families', len(both), 405),
    ('  second family cheaper', len(cheaper2), 403),
    ('  mean saving (%)', round(100 * sum((c1(m) - c2(m)) / c1(m) for m in cheaper2) / len(cheaper2), 1), 7.3),
    ('degrees without irreducible trinomials', len(noT), 502),
    ('  covered by second family', sum(m in F2 for m in noT), 288),
    ('  covered by first family', sum(m in F1 for m in noT), 229),
    ('  covered by second family only', sum(m in F2 and m not in F1 for m in noT), 112),
    ('  covered by neither', sum(m not in F2 and m not in F1 for m in noT), 161),
    ('mean cost per bit, best generic second-family member', round(sum(best_gen(m) / m for m in gen) / len(gen), 2), 2.77),
]
for label, got, want in rows:
    good = got == want; ok &= good
    print(f"  {'ok ' if good else 'BAD'} {label}: {got}" + ('' if good else f' (paper: {want})'))
others = sorted((m, c1(m), c2(m)) for m in both if c2(m) >= c1(m))
print(f'  degrees where the second family is not cheaper: {others}  (paper: m=155 first cheaper, m=5 tie)')
print('\nALL OK' if ok else '\nSOME VALUES DIFFER')
sys.exit(0 if ok else 1)
