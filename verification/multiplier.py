#!/usr/bin/env python3
"""Table 10 (Section IX-D): XOR gates of a full multiplier and of a squaring at degrees 163
and 571. Product: schoolbook ((m-1)^2 XOR) or the recursive Karatsuba multiplier of
karatsuba.py (built explicitly and tested on random inputs). Reduction: Theorem 8 for the
second family, BCP's 3m-2 for the first family, greedy count for the NIST pentanomial.
Squaring: greedy count of the reduction of a square (./greedy sq). About 2 minutes."""
import os, subprocess, json
here = os.path.dirname(os.path.abspath(__file__)); os.chdir(here)
from karatsuba import best_plan, check, cost
plan = best_plan(571)
K = {}
for m in (163, 571):
    ok, P = check(m, plan)
    K[m] = (P.nx, P.na, ok)
    print(f"Karatsuba product m={m}: correct={ok} XOR={P.nx} AND={P.na}")
def g(mode, ex):
    out = subprocess.run(['./greedy', mode, '0'] + list(map(str, ex)), capture_output=True, text=True).stdout
    return int(out.split('CX=')[1].split()[0])
polys = {163: {'second': ((71, 46), 3 * 163 - 46 - 3), 'first': ((74, 15), 3 * 163 - 2), 'NIST': ([163, 7, 6, 3, 0], None)},
         571: {'second': ((207, 182), 3 * 571 - 182 - 3), 'first': ((218, 135), 3 * 571 - 2), 'NIST': ([571, 10, 5, 2, 0], None)}}
rows = {}
for m, D in polys.items():
    for name, (p, red) in D.items():
        if name == 'second': ex = [m, p[0] + p[1], p[0], p[1], 0]
        elif name == 'first': ex = [m, p[0] + p[1], p[0], p[1], 0]
        else: ex = p
        if red is None: red = g('one', ex)
        sq = g('sq', ex)
        rows[f"{m} {name}"] = (red, (m - 1) ** 2 + red, K[m][0] + red, sq)
        print(f"m={m} {name:7s} reduction {red:5d} schoolbook {(m-1)**2+red:7d} Karatsuba {K[m][0]+red:6d} squaring {sq:4d}")
for m in (163, 571):
    s2 = rows[f"{m} second"]
    for o in ('first', 'NIST'):
        r = rows[f"{m} {o}"]
        print(f"m={m} saving vs {o}: reduction {100*(r[0]-s2[0])/r[0]:.1f}%  Karatsuba multiplier {100*(r[2]-s2[2])/r[2]:.2f}%  squaring {100*(r[3]-s2[3])/r[3]:.1f}%")
json.dump({'karatsuba': K, 'rows': rows}, open('multiplier.json', 'w'))
