#!/usr/bin/env python3
"""Compose the greedy strip programs (Section III) over all strips of every special member
with m <= MMAX and check each result symbolically against the reduction matrix.
Usage: python3 compose_strips.py [MMAX] [RUNS]   (defaults 1100, 200)"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'generator'))
import strips

def rows_fast(f, top):
    m = f.bit_length() - 1; rows = [set() for _ in range(m)]; r = 1
    for j in range(top + 1):
        if j > 0:
            r <<= 1
            if r >> m & 1:
                r ^= f
        x, i = r, 0
        while x:
            if x & 1:
                rows[i].add(j)
            x >>= 1; i += 1
    return rows

strips.rows_of = rows_fast
mmax = int(sys.argv[1]) if len(sys.argv) > 1 else 1100
runs = int(sys.argv[2]) if len(sys.argv) > 2 else 200
total = bad = 0
for bp, cp in [(2, 1), (3, 1), (4, 1), (5, 1), (3, 2)]:
    k = bp + 2 * cp; G = strips.fam(bp, cp)
    P1 = strips.best(rows_fast(G, 2 * k - 1), runs)
    P2 = strips.best(rows_fast(G, 2 * k - 2), runs)
    print(f"G=f_({bp},{cp}): R1={strips.cost(P1)} R2={strips.cost(P2)}", flush=True)
    for g in range(1, mmax // k + 1):
        ok, ng, closed = strips.compose_and_check(bp, cp, g, P1, P2)
        total += 1
        if not ok or ng != (g - 1) * strips.cost(P1) + strips.cost(P2):
            bad += 1; print("BAD", bp, cp, g, ok, ng, flush=True)
print("composed and checked:", total, "failures:", bad)
