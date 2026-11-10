#!/usr/bin/env python3
"""Gate counts of a bit-parallel polynomial multiplier over F_2 (product of two polynomials
with n coefficients, giving 2n-1 coefficients), built recursively: at each size the cheapest
of the schoolbook product, the Karatsuba split and Bernstein's refined Karatsuba split is
used, minimizing the number of 2-input XOR gates plus AND gates. Every program is built
explicitly and tested on random inputs; gate counts and XOR depth are read from the program.
Usage: python3 karatsuba.py n [n ...]"""
import random, sys
from functools import lru_cache
sys.setrecursionlimit(10000)

class Prog:
    def __init__(s, n):
        s.n = n; s.ops = []; s.depth = {}; s.nx = s.na = 0
        for i in range(n): s.depth[('a', i)] = s.depth[('b', i)] = 0
    def AND(s, u, v):
        s.na += 1; w = ('g', len(s.ops)); s.ops.append(('&', u, v, w)); s.depth[w] = 0; return w
    def XOR(s, u, v):
        if u is None: return v
        if v is None: return u
        s.nx += 1; w = ('g', len(s.ops)); s.ops.append(('^', u, v, w)); s.depth[w] = max(s.depth[u], s.depth[v]) + 1; return w

def padd(P, X, Y):          # coefficient-wise sum of two lists (None = 0)
    L = max(len(X), len(Y)); X = X + [None] * (L - len(X)); Y = Y + [None] * (L - len(Y))
    return [P.XOR(x, y) for x, y in zip(X, Y)]
def shift(X, k): return [None] * k + X

def school(P, A, B):
    n = len(A); C = [None] * (2 * n - 1)
    for i in range(n):
        for j in range(n):
            C[i + j] = P.XOR(C[i + j], P.AND(A[i], B[j]))
    return C

def mult(P, A, B, plan):
    n = len(A)
    kind = plan[n]
    if kind == 'S': return school(P, A, B)
    h = (n + 1) // 2
    A0, A1, B0, B1 = A[:h], A[h:], B[:h], B[h:]
    P0 = mult(P, A0, B0, plan); P2 = mult(P, A1, B1, plan) if n - h > 0 else []
    SA = padd(P, A0, A1); SB = padd(P, B0, B1)
    P1 = mult(P, SA, SB, plan)
    if kind == 'K':          # C = P0 + x^h (P1 + P0 + P2) + x^2h P2
        M = padd(P, padd(P, P1, P0), P2)
        return padd(P, padd(P, P0, shift(M, h)), shift(P2, 2 * h))[:2 * n - 1]
    # 'R': refined Karatsuba (Bernstein): T = P0 + x^h P2; C = T + x^h T + x^h P1
    T = padd(P, P0, shift(P2, h))
    return padd(P, padd(P, T, shift(T, h)), shift(P1, h))[:2 * n - 1]

def cost(n, plan):
    P = Prog(n); C = mult(P, [('a', i) for i in range(n)], [('b', i) for i in range(n)], plan)
    return P, C

def best_plan(N):
    plan = {}
    for n in range(1, N + 1):
        best = None
        for kind in (['S'] if n == 1 else ['S', 'K', 'R']):
            plan[n] = kind
            P, _ = cost(n, plan)
            key = (P.nx + P.na, P.nx)
            if best is None or key < best[0]: best = (key, kind)
        plan[n] = best[1]
    return plan

def check(n, plan, trials=200):
    P, C = cost(n, plan)
    for _ in range(trials):
        a = random.getrandbits(n); b = random.getrandbits(n)
        val = {}
        for i in range(n): val[('a', i)] = a >> i & 1; val[('b', i)] = b >> i & 1
        for op, u, v, w in P.ops: val[w] = (val[u] & val[v]) if op == '&' else (val[u] ^ val[v])
        prod = 0
        for i in range(n):
            if b >> i & 1: prod ^= a << i
        got = sum((val[c] if c is not None else 0) << k for k, c in enumerate(C))
        if got != prod: return False, P
    return True, P

if __name__ == '__main__':
    ns = [int(x) for x in sys.argv[1:]] or [163, 571]
    plan = best_plan(max(ns))
    for n in ns:
        ok, P = check(n, plan)
        d = max(P.depth[c] for c in cost(n, plan)[1] if c is not None)
        print(f"n={n}: correct={ok} XOR={P.nx} AND={P.na} XOR-depth={d}  schoolbook XOR={(n-1)**2} AND={n*n}")
