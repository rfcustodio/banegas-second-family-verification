#!/usr/bin/env python3
"""Strip programs for the special members of Banegas' second family.

For f = f_{b,c} = G(x^gamma), gamma = gcd(b, c), G = f_{b',c'} of degree kappa,
reduction modulo f splits into gamma independent reductions modulo G
(Proposition 4 of the paper). This script

  1. searches short programs for the two strip reductions modulo G
     (inputs of degree 2*kappa-1 and 2*kappa-2) with greedy pair substitution,
     lexicographic and randomized tie-breaking;
  2. composes them over the strips of f and checks the result symbolically
     against the reduction matrix of f;
  3. sweeps all reduced pairs (b', c') with 4 <= k <= KMAX and reports which
     base polynomials admit strip programs shorter than the closed form
     (with the greedy search; the optimal values of Table 2 come from SAT,
     see verification/exact_base.py).

Usage: python3 strips.py [KMAX] [RUNS]   (defaults: 21 and 200)
       python3 strips.py --special MMAX    (Table 8: irreducible special
                                             members with 5 <= m <= MMAX)
"""
import itertools, math, random, sys

def polymod(a, f):
    df = f.bit_length() - 1
    while a.bit_length() - 1 >= df:
        a ^= f << (a.bit_length() - 1 - df)
    return a

def fam(b, c):
    m = b + 2 * c
    return (1 << m) | (1 << (b + c)) | (1 << b) | (1 << c) | 1

def rows_of(f, top):
    """Row i lists the inputs j <= top whose residue x^j mod f contains x^i."""
    m = f.bit_length() - 1
    rows = [set() for _ in range(m)]
    for j in range(top + 1):
        r = polymod(1 << j, f)
        for i in range(m):
            if r >> i & 1:
                rows[i].add(j)
    return rows

TMP = 10 ** 6

def greedy(rows, seed=None):
    rows = [set(r) for r in rows]
    rnd = random.Random(seed)
    gates, nxt = [], TMP
    while True:
        freq = {}
        for r in rows:
            for p in itertools.combinations(sorted(r), 2):
                freq[p] = freq.get(p, 0) + 1
        if not freq or max(freq.values()) < 2:
            break
        mx = max(freq.values())
        cands = sorted(p for p, v in freq.items() if v == mx)
        p = cands[0] if seed is None else rnd.choice(cands)
        for r in rows:
            if p[0] in r and p[1] in r:
                r -= set(p); r.add(nxt)
        gates.append((nxt, p[0], p[1])); nxt += 1
    return gates, rows

def cost(prog):
    gates, rows = prog
    return len(gates) + sum(len(r) - 1 for r in rows if r)

def best(rows, runs):
    progs = [greedy(rows)] + [greedy(rows, s) for s in range(runs)]
    return min(progs, key=cost)

def compose_and_check(bp, cp, gamma, P1, P2):
    k = bp + 2 * cp; m = gamma * k; b, c = gamma * bp, gamma * cp
    outs, ngates = [None] * m, 0
    for r in range(gamma):
        gates, rows = P2 if r == gamma - 1 else P1
        env = {}
        val = lambda v: env[v] if v >= TMP else frozenset([r + gamma * v])
        for t, a, a2 in gates:
            env[t] = val(a) ^ val(a2); ngates += 1
        for i, row in enumerate(rows):
            acc = frozenset()
            for v in row:
                acc ^= val(v)
            ngates += max(0, len(row) - 1)
            outs[r + gamma * i] = acc
    target = rows_of(fam(b, c), 2 * m - 2)
    ok = all(outs[i] == frozenset(target[i]) for i in range(m))
    return ok, ngates, 3 * m - c - 3

def main():
    kmax = int(sys.argv[1]) if len(sys.argv) > 1 else 21
    runs = int(sys.argv[2]) if len(sys.argv) > 2 else 200
    print("k  (b',c')  R2  3k-c'-3  R1  3k-c'  shorter?")
    special = []
    for k in range(4, kmax + 1):
        for cp in range(1, k):
            bp = k - 2 * cp
            if bp <= cp or math.gcd(bp, cp) != 1:
                continue
            G = fam(bp, cp)
            P1 = best(rows_of(G, 2 * k - 1), runs)
            P2 = best(rows_of(G, 2 * k - 2), runs)
            R1, R2 = cost(P1), cost(P2)
            short = R1 < 3 * k - cp or R2 < 3 * k - cp - 3
            print(f"{k:2d} ({bp},{cp})  {R2:3d}  {3*k-cp-3:3d}  {R1:3d}  {3*k-cp:3d}  {'yes' if short else 'no'}")
            if short:
                special.append((bp, cp, P1, P2))
    print("\nComposition check over strips (gamma = 1..7):")
    for bp, cp, P1, P2 in special:
        for g in range(1, 8):
            ok, n, closed = compose_and_check(bp, cp, g, P1, P2)
            print(f"  G=f_({bp},{cp}) gamma={g}: {n} gates (closed form {closed}), correct={ok}")


# ---------------------------------------------------------------------------
# Table 8: irreducible special members (Proposition 19) and their costs.

def mulmod(a, b, f):
    r, fb = 0, f.bit_length()
    while b:
        if b & 1:
            r ^= a
        b >>= 1; a <<= 1
        if a.bit_length() == fb:
            a ^= f
    return r

def pgcd(a, b):
    while b:
        a, b = b, polymod(a, b)
    return a

def rabin(f):
    m = f.bit_length() - 1
    def frob(e):
        t = 2
        for _ in range(e):
            t = mulmod(t, t, f)
        return t
    primes = [p for p in range(2, m + 1) if m % p == 0
              and all(p % q for q in range(2, int(p ** 0.5) + 1))]
    return frob(m) == 2 and all(pgcd(f, frob(m // p) ^ 2) == 1 for p in primes)

BASE = {(2, 1): (6, 7), (3, 1): (10, 12), (4, 1): (14, 15),
        (5, 1): (16, 18), (3, 2): (16, 18)}   # (R2, R1), optimal values of Table 2

def chain_N(b, c):
    """N(b,c) of Theorem 13 (chain construction)."""
    return c * ((b + c) // (3 * c)) + max(0, (b + c) % (3 * c) - 2 * c)

def special_table(mmax):
    rows = []
    for (bp, cp), (R2, R1) in BASE.items():
        k = bp + 2 * cp
        for g in range(1, mmax // k + 1):
            m, b, c = g * k, g * bp, g * cp
            if m >= 5 and rabin(fam(b, c)):
                rows.append((m, bp, cp, g, b, c, 3 * m - c - 3, (g - 1) * R1 + R2))
    print(" m   G       gamma  closed  strips  best generic")
    for m, bp, cp, g, b, c, closed, strip in sorted(rows):
        gen = None
        for cc in range(1, (m - 1) // 3 + 1):
            bb = m - 2 * cc
            gg = math.gcd(bb, cc)
            if bb <= cc or (bb // gg, cc // gg) in BASE:
                continue
            if rabin(fam(bb, cc)):
                cost = min(3 * m - cc - 3, 3 * m - 3 - chain_N(bb, cc))   # Theorems 8 and 13
                gen = cost if gen is None else min(gen, cost)
        print(f"{m:4d} f_({bp},{cp}) {g:5d} {closed:7d} {strip:7d}  {gen if gen else 'none'}")

if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "--special":
        special_table(int(sys.argv[2]))
    else:
        main()
