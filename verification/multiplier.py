#!/usr/bin/env python3
"""Table 10 (Section IX-E): XOR gates of a full multiplier and of a squaring at degrees 163
and 571, for EVERY irreducible member of the two families (read from data/fam2_irr.txt and
data/fam1_irr.txt) and for the NIST pentanomial. Product: schoolbook ((m-1)^2 XOR) or the
recursive Karatsuba multiplier of karatsuba.py (built explicitly and tested on random
inputs). Reduction: the better of Theorems 8 and 13 for the second family, BCP's 3m-2 for
the first family, greedy count for the NIST pentanomial. Squaring: greedy count of the
reduction of a square (./greedy sq), lexicographic ties, and the best of 20 randomized runs.
The modulus with the smallest reduction bound need not have the smallest squaring count, so
the squaring comparison is made separately over all members. About 2 minutes."""
import os, subprocess, json
here = os.path.dirname(os.path.abspath(__file__)); os.chdir(here)
from karatsuba import best_plan, check, cost
plan = best_plan(571)
K = {}
for m in (163, 571):
    ok, P = check(m, plan)
    K[m] = (P.nx, P.na, ok)
    print(f"Karatsuba product m={m}: correct={ok} XOR={P.nx} AND={P.na}")
def g(mode, ex, runs=0):
    out = subprocess.run(['./greedy', mode, str(runs)] + list(map(str, ex)), capture_output=True, text=True).stdout
    return int(out.split('CX=')[1].split()[0]), int(out.split('bestRandom=')[1].split()[0])
def N(b, c): return c * ((b + c) // (3 * c)) + max(0, ((b + c) % (3 * c)) - 2 * c)
def members(fn, m):
    return [tuple(map(int, l.split()))[1:] for l in open(os.path.join("..", "data", fn)) if l.split() and int(l.split()[0]) == m]
NIST = {163: [163, 7, 6, 3, 0], 571: [571, 10, 5, 2, 0]}
RUNS = 20
rows = {}
best = {}
for m in (163, 571):
    L = [('second', b, c, min(3 * m - c - 3, 3 * m - 3 - N(b, c))) for b, c in sorted(members('fam2_irr.txt', m), key=lambda p: -p[1])]
    L += [('first', b, c, (12 * m) // 5 - 1 if b == 2 * c else 3 * m - 2) for b, c in sorted(members('fam1_irr.txt', m), key=lambda p: p[1])]
    L += [('NIST', None, None, None)]
    for name, b, c, red in L:
        ex = NIST[m] if name == 'NIST' else [m, b + c, b, c, 0]
        if red is None: red = g('one', ex)[0]
        sq, sqr = g('sq', ex, RUNS)
        label = f"{m} {name}" + ("" if name == 'NIST' else f" ({b},{c})")
        rows[label] = (red, (m - 1) ** 2 + red, K[m][0] + red, sq, sqr)
        print(f"m={m} {name:6s} {'' if name == 'NIST' else '(%d,%d)' % (b, c):10s} reduction {red:5d} schoolbook {(m-1)**2+red:7d} "
              f"Karatsuba {K[m][0]+red:6d} squaring {sq:4d} (best of {RUNS} randomized runs: {sqr})")
        for col, v in (('red', red), ('sq', sq)):
            k = (m, name, col)
            if k not in best or v < best[k][0]: best[k] = (v, label, K[m][0] + red)
pct = lambda a, b: 100 * (b - a) / b
for m in (163, 571):
    r2, rn = best[(m, 'second', 'red')], best[(m, 'NIST', 'red')]
    r1 = best[(m, 'first', 'red')]
    print(f"m={m} reduction, best second vs first: {pct(r2[0], r1[0]):.1f}%  vs NIST: {pct(r2[0], rn[0]):.1f}%; "
          f"Karatsuba multiplier vs first: {pct(r2[2], r1[2]):.2f}%  vs NIST: {pct(r2[2], rn[2]):.2f}%")
    s2, s1, sn = best[(m, 'second', 'sq')][0], best[(m, 'first', 'sq')][0], best[(m, 'NIST', 'sq')][0]
    print(f"m={m} squaring, minimized separately in each family: second {s2}, first {s1}, NIST {sn}; "
          f"second relative to first: {100*(s2-s1)/s1:+.1f}% gates; "
          f"second vs NIST: {pct(s2, sn):.1f}%; first vs NIST: {pct(s1, sn):.1f}%")
json.dump({'karatsuba': K, 'rows': rows}, open('multiplier.json', 'w'))
