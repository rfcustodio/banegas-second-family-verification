#!/usr/bin/env python3
"""Section IX-C and Table 7: comparison with other pentanomial families over the 502 degrees
5 <= m <= 1100 without irreducible trinomials.

Inputs (written by run_all.sh with ./census): sec.txt, fst.txt, tri.txt, and
  t1.txt   irreducible type I  x^m+x^{n+1}+x^n+x+1         (census t1 5 1100)
  t2.txt   irreducible type II x^m+x^{n+2}+x^{n+1}+x^n+1    (census t2 5 1100)
  esp.txt  irreducible x^m+x^{m-s}+x^{m-2s}+x^{m-3s}+1       (census esp 5 1100)
  pmin.txt first irreducible x^m+x^k3+x^k2+x^k1+1, k3<=m/2   (census pmin 5 1100)
The type II cost is the greedy count (./greedy one 0 ...), minimized over the irreducible
members of each degree. Writes other_families.json and prints the numbers of the paper."""
import json, math, os, statistics as st, subprocess, sys
here = os.path.dirname(os.path.abspath(__file__)); os.chdir(here)
def load(fn):
    D = {}
    for l in open(fn):
        a = list(map(int, l.split())); D.setdefault(a[0], []).append(a[1:])
    return D
tri = {m for m, v in load('tri.txt').items() if v[0][0] > 0}
noT = [m for m in range(5, 1101) if m not in tri]
sec, fst = load('sec.txt'), load('fst.txt')
t1, t2, esp, pmin = load('t1.txt'), load('t2.txt'), load('esp.txt'), load('pmin.txt')
SPEC = {(2, 1): (6, 7), (3, 1): (10, 12), (4, 1): (14, 15), (5, 1): (16, 18), (3, 2): (16, 18)}
N = lambda b, c: c * ((b + c) // (3 * c)) + max(0, (b + c) % (3 * c) - 2 * c)
def c2(m, b, c):
    g = math.gcd(b, c); v = min(3 * m - c - 3, 3 * m - 3 - N(b, c))
    if (b // g, c // g) in SPEC: R2, R1 = SPEC[(b // g, c // g)]; v = min(v, (g - 1) * R1 + R2)
    return v
def greedy(ex):
    out = subprocess.run(['./greedy', 'one', '0'] + list(map(str, ex)), capture_output=True, text=True).stdout
    return int(out.split('CX=')[1].split()[0])
C = {'second': {m: min(c2(m, b, c) for b, c in sec[m]) for m in noT if m in sec},
     'first': {m: min(12 * m // 5 - 1 if b == 2 * c else 3 * m - 2 for b, c in fst[m]) for m in noT if m in fst},
     'typeI': {m: 3 * m - 2 for m in noT if m in t1},
     'typeII': {m: min(greedy([m, n + 2, n + 1, n, 0]) for (n,) in t2[m]) for m in noT if m in t2},
     'k3<=m/2': {m: 4 * (m - 1) for m in noT if m in pmin and pmin[m][0][0] > 0}}
S = C['second']
print(f"degrees without irreducible trinomials: {len(noT)}")
print(f"{'family':10s} {'degrees':>7s} {'XOR/bit':>7s} {'shared':>6s} {'2nd cheaper':>11s} {'mean saving':>11s}")
for f, D in C.items():
    sh = [m for m in D if m in S]
    sav = f"{100 * st.mean((D[m] - S[m]) / D[m] for m in sh):.1f}%" if f != 'second' else ''
    print(f"{f:10s} {len(D):7d} {st.mean(D[m] / m for m in D):7.2f} {len(sh) if f != 'second' else '':>6} "
          f"{sum(S[m] < D[m] for m in sh) if f != 'second' else '':>11} {sav:>11s}")
best = {m: min(C[f][m] for f in C if f != 'second' and m in C[f]) for m in S}
rel = [(best[m] - S[m]) / best[m] for m in S]
print(f"second family cheaper than every other family in {sum(r > 0 for r in rel)} of {len(S)} degrees: "
      f"{100 * min(rel):.1f}% to {100 * max(rel):.1f}%, mean {100 * st.mean(rel):.1f}%")
fam4 = ('second', 'first', 'typeI', 'typeII')
cov = [m for m in noT if any(m in C[f] for f in fam4)]
only = [m for m in S if not any(m in C[f] for f in fam4[1:])]
print(f"covered by the four families: {len(cov)}; by the second family only: {len(only)} {only[:4]}")
print(f"class x^m+x^(m-s)+x^(m-2s)+x^(m-3s)+1: irreducible members in degrees without trinomials: {sum(m in esp for m in noT)}")
print("NIST degrees (typeI, typeII):", {m: (C['typeI'].get(m), C['typeII'].get(m)) for m in (163, 283, 571)})
json.dump({f: {str(m): v for m, v in D.items()} for f, D in C.items()}, open('other_families.json', 'w'))
