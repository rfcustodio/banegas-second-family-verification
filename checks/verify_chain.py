#!/usr/bin/env python3
"""Checks the chain construction of Section VI (Lemma 12, Algorithm 2, Theorem 13,
Example 14, Proposition 15) on every member b > c >= 1 with m <= MMAX, symbolically
(the program's outputs are compared with the rows of the reduction matrix), using the
generator algorithm2/alg2prog.py. Standard library only.
Usage: python3 checks/verify_chain.py [--mmax 120]     (the full range m <= 1100 is
checked in C by verification/run_all.sh)
"""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'algorithm2'))
from alg2prog import program, check

MMAX = int(sys.argv[sys.argv.index('--mmax') + 1]) if '--mmax' in sys.argv else 120
ok_all = True
def report(label, good, detail=''):
    global ok_all
    ok_all &= good
    print(f"  {'PASS' if good else 'FAIL'}  {label}" + (f'  {detail}' if detail else ''))

def N(b, c):
    return sum(1 for u in range(1, b + c) if (u // c) % 3 == 2)
def N_closed(b, c):
    return c * ((b + c) // (3 * c)) + max(0, (b + c) % (3 * c) - 2 * c)

# Lemma 12: E_t = h_t + P_{t+2c}, P_k = h_{k-c} + E_{k+c}, P_k = E_{k-c} + E_k,
# with h_s as bit masks and C_t the comb sums of Definition 6.
bad = 0; cnt = 0
for m in range(4, min(MMAX, 80) + 1):
    for c in range(1, (m - 1) // 3 + 1):
        b = m - 2 * c
        if b <= c: continue
        n = m - 2
        h = lambda s: (1 << s) if 0 <= s <= n else 0
        Cm = {}
        def C(t):
            if t > n: return 0
            if t not in Cm: Cm[t] = h(t) ^ C(t + 3 * c)
            return Cm[t]
        E = lambda t: C(t) ^ C(t + c)
        P = lambda k: C(k - c) ^ C(k + c)
        for t in range(0, n + 2 * c):
            cnt += 1
            bad += E(t) != h(t) ^ P(t + 2 * c)
            if t >= c: bad += (P(t) != h(t - c) ^ E(t + c)) + (P(t) != E(t - c) ^ E(t))
            if t > n - c: bad += E(t) != h(t)
            if t >= c and t > n - c: bad += P(t) != h(t - c)
report(f'Lemma 12 identities ({cnt} index pairs, m <= {min(MMAX, 80)})', bad == 0)

# Theorem 13 and Proposition 15 on every member with m <= MMAX
members = fails = wrongN = improved = 0; maxdepthexcess = -99
for m in range(4, MMAX + 1):
    for c in range(1, (m - 1) // 3 + 1):
        b = m - 2 * c
        if b <= c: continue
        members += 1
        correct, gates, formula, depth = check(b, c)
        n = m - 2
        if not correct or gates != formula or gates != 3 * m - 3 - N(b, c): fails += 1
        if N(b, c) != N_closed(b, c): wrongN += 1
        if (N(b, c) > c) != (b >= 4 * c + 1): wrongN += 1
        if (N(b, c) == c) != (2 * c <= b <= 4 * c): wrongN += 1
        if formula > 8 * m / 3 + c - 3: wrongN += 1
        improved += formula < 3 * m - c - 3
        maxdepthexcess = max(maxdepthexcess, depth - (2 * ((n - c) // (3 * c)) + 6))
report(f'Theorem 13: Algorithm 2 correct with exactly 3m-3-N(b,c) gates ({members} members, m <= {MMAX})', fails == 0)
report('Theorem 13: closed formula for N, cases b<2c / 2c<=b<=4c / b>=4c+1, bound 8m/3+c-3', wrongN == 0)
report('Proposition 15: depth <= 2*floor((n-c)/3c)+6', maxdepthexcess <= 0, f'(max depth - bound = {maxdepthexcess}; the paper reports at most -1 up to m = 1100)')
print(f'        members improved over 3m-c-3: {improved} of {members}')

# Example 14 and the values quoted in Sections VI and VIII
for (b, c), want in (((8, 1), 24), ((6, 1), 19), ((5, 1), 16), ((7, 1), 22), ((9, 1), 27), ((5, 2), 22), ((7, 2), 28)):
    correct, gates, formula, depth = check(b, c)
    report(f'f_({b},{c}): {gates} gates (paper: {want})', correct and gates == want)
prog, *_ = program(8, 1)
report('Example 14: 12 gates before the outputs', sum(1 for g in prog if g[0][0] in 'EP') == 12)
for (b, c), want in (((201, 16), 632), ((527, 22), 1534)):
    correct, gates, formula, depth = check(b, c)
    report(f'Table 4, last column: b={b}, c={c}: {gates} gates (paper: {want})', correct and gates == want)
correct, gates, formula, depth = check(527, 22)
report('Section VI: m = 571, c = 22 has depth 20', depth == 20)
print('\nALL OK' if ok_all else '\nSOME CHECKS FAILED')
sys.exit(0 if ok_all else 1)
