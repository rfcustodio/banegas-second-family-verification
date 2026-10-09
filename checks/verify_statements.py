#!/usr/bin/env python3
"""Checks, statement by statement, the mathematical claims of the paper
"Banegas' Second Family of Irreducible Pentanomials: a Closed-Form Reduction with
3m - c - 3 XOR Gates" (paper/artigo2.tex).

Every check is self-contained (plain Python 3, no third-party packages) except the
checks of Theorem 6, Proposition 7 and Example 9, which run the authors' generator in
generator/fam2.py.  Numbering follows the compiled paper (paper/artigo2.pdf).

Usage:
  python3 checks/verify_statements.py            # default range m <= 120 (about 1-2 min)
  python3 checks/verify_statements.py --mmax 300 # the range used in the paper (slower)
"""
import argparse, random, sys
from math import gcd
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'generator'))

# ----------------------------------------------------------------- GF(2)[x] helpers
def pmul(a, b):
    r = 0
    while b:
        if b & 1: r ^= a
        a <<= 1; b >>= 1
    return r

def pdivmod(a, f):
    df = f.bit_length() - 1; q = 0
    while a and a.bit_length() - 1 >= df:
        s = a.bit_length() - 1 - df
        q ^= 1 << s; a ^= f << s
    return q, a

def poly(*exps):
    p = 0
    for e in exps: p ^= 1 << e
    return p

def f2(b, c):
    return poly(b + 2 * c, b + c, b, c, 0)

def members(mmax, mmin=4):
    for m in range(mmin, mmax + 1):
        for c in range(1, m):
            b = m - 2 * c
            if b > c: yield m, b, c

def reduction_rows(f):
    m = f.bit_length() - 1; rows = [0] * m; col = 1
    for j in range(2 * m - 1):
        t, i = col, 0
        while t:
            if t & 1: rows[i] |= 1 << j
            t >>= 1; i += 1
        col <<= 1
        if col >> m & 1: col ^= f
    return rows

RESULTS = []
def report(name, ok, detail):
    RESULTS.append((name, ok))
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}", flush=True)

# ----------------------------------------------------------------- Proposition 2
def check_prop2(mmax):
    n = 0; bad = []
    for m, b, c in members(mmax):
        f = f2(b, c); n += 1
        i_ok = pdivmod(1 << m, f)[1] == pdivmod(pmul(poly(b, 0), poly(c, 0)), f)[1]
        ii_ok = pmul(poly(c, 0), f) == poly(b + 3 * c, b, 2 * c, 0) and \
            pdivmod(pmul(1 << b, poly(3 * c, 0)), f)[1] == pdivmod(pmul(poly(c, 0), poly(c, 0)), f)[1]
        iii_ok = 1 <= c <= (m - 1) // 3 and (m - b) % 2 == 0
        g = gcd(b, c)
        if g > 1:
            G = f2(b // g, c // g)
            Gx = 0
            for e in range(G.bit_length()):
                if G >> e & 1: Gx ^= 1 << (e * g)
            iv_ok = Gx == f
        else:
            iv_ok = True
        v_ok = (b != 2 * c) or f == poly(4 * c, 3 * c, 2 * c, c, 0)
        if not (i_ok and ii_ok and iii_ok and iv_ok and v_ok): bad.append((m, b, c))
    report('Proposition 2 (i)-(v)', not bad, f'{n} members with m <= {mmax}, failures: {bad[:5]}')

# ----------------------------------------------------------------- Lemma 3 (numeric)
def check_lemma3(mmax, trials=5):
    rng = random.Random(3); n = 0; bad = []
    for m, b, c in members(mmax):
        f = f2(b, c); S = [c, b, b + c]
        for _ in range(trials):
            D = rng.getrandbits(2 * m - 1); Q, R = pdivmod(D, f); n += 1
            q = lambda k: (Q >> k) & 1 if 0 <= k <= m - 2 else 0
            d = lambda k: (D >> k) & 1
            ok = all(d(m + j) == (q(j) ^ sum(q(j + m - e) for e in S) % 2) for j in range(m - 1)) and \
                 all((R >> i) & 1 == (d(i) ^ sum(q(i - e) for e in S + [0]) % 2) for i in range(m))
            if not ok: bad.append((m, b, c)); break
    report('Lemma 3 (division identities, eqs. 2-3)', not bad, f'{n} random products, failures: {bad[:5]}')

# ----------------------------------------------------------------- Theorem 5 (symbolic)
def check_thm5(mmax):
    """q_j as linear forms in h (bitmask over h-indices) obtained from recurrence (4),
    compared with the closed forms (5)-(7)."""
    n_ok = 0; bad = []
    for m, b, c in members(mmax):
        n = m - 2
        q = [0] * (n + 1)
        for j in range(n, -1, -1):                       # recurrence (4), top-down
            v = 1 << j
            for e in (c, 2 * c, b + c):
                if j + e <= n: v ^= q[j + e]
            q[j] = v
        H = lambda s: (1 << s) if 0 <= s <= n else 0
        C = {}
        for t in range(n, -1, -1):
            C[t] = H(t) ^ (C[t + 3 * c] if t + 3 * c <= n else 0)
        Cg = lambda t: C.get(t, 0) if t >= 0 else 0
        ok = all(q[j] == Cg(j) ^ Cg(j + c) ^ H(j + b + c) for j in range(n + 1))      # (5)
        qq = lambda k: q[k] if 0 <= k <= n else 0
        for k in range(m):                                                            # (6)
            U = qq(k) ^ qq(k - c)
            Uc = (Cg(k) ^ Cg(k + c) ^ H(k + b + c)) if k < c else (Cg(k - c) ^ Cg(k + c) ^ H(k + b))
            ok &= U == Uc
        # (7): r_i = d_i + U_i + U_{i-b}, in terms of input bits d (h_s = d_{m+s})
        rows = reduction_rows(f2(b, c))
        Uf = lambda k: (qq(k) ^ qq(k - c)) if k >= 0 else 0
        for i in range(m):
            form = (1 << i) | ((Uf(i) ^ Uf(i - b)) << m)
            ok &= form == rows[i]
        if ok: n_ok += 1
        else: bad.append((m, b, c))
    report('Theorem 5 (closed-form quotient, eqs. 5-7)', not bad, f'{n_ok} members with m <= {mmax}, failures: {bad[:5]}')

# ----------------------------------------------------------------- Theorem 6, Prop. 7 (generator)
def check_thm6_prop7(mmax):
    from fam2 import program, check
    n = 0; bad6 = []; bad7 = []; plus3 = tot3 = 0
    for m, b, c in members(mmax):
        P, out = program(b, c); n += 1
        if not check(b, c, P, out) or len(P.gates) > 3 * m - c - 3: bad6.append((m, b, c))
        d = max(P.depth[o] for o in out)
        if d > (m - 2) // (3 * c) + 4: bad7.append((m, b, c))
        if 7 <= m < 300:
            tot3 += 1; plus3 += d == (m - 2) // (3 * c) + 3
    report('Theorem 6 (Algorithm 1 correct, <= 3m-c-3 XORs)', not bad6, f'{n} members, failures: {bad6[:5]}')
    report('Proposition 7 (depth <= floor(n/3c)+4)', not bad7, f'{n} members, failures: {bad7[:5]}')
    print(f'       measured depth == floor(n/3c)+3 in {plus3} of {tot3} members with 7 <= m < min(300, mmax+1) '
          f'(paper, with --mmax 300: 14,285 of 14,748, i.e. 97%)')

# ----------------------------------------------------------------- Corollary 10 and Corollary 8
def word_reduce(D, b, c):
    m = b + 2 * c; n = m - 2; mask = (1 << m) - 1
    L, H = D & mask, D >> m
    C, s = H, 3 * c
    while s <= n:
        C ^= C >> s; s *= 2
    Q = C ^ (C >> c) ^ (H >> (b + c))
    U = Q ^ (Q << c)
    return (L ^ U ^ (U << b)) & mask

def check_cor10_cor8(mmax, trials=5):
    rng = random.Random(10); n = 0; bad = []
    for m, b, c in members(mmax):
        f = f2(b, c)
        for _ in range(trials):
            A, B = rng.getrandbits(m), rng.getrandbits(m)
            D = pmul(A, B); n += 1                    # schoolbook carry-less product
            if word_reduce(D, b, c) != pdivmod(D, f)[1]: bad.append((m, b, c)); break
    report('Corollary 10 (word-level reduction) + multiplier of Corollary 8', not bad,
           f'{n} random field products, failures: {bad[:5]}')
    ident = all((m - 1) ** 2 + 3 * m - c - 3 == m * m + m - c - 2 for m, b, c in members(mmax))
    report('Corollary 8 (XOR count identity (m-1)^2+3m-c-3 = m^2+m-c-2)', ident, 'algebraic identity checked')

# ----------------------------------------------------------------- Example 9
def check_example9():
    from fam2 import program, check
    from contaxor import irredutivel, matriz_reducao, conta_xor
    b, c = 6, 5; f = f2(b, c)
    P, out = program(b, c)
    rows = reduction_rows(f)
    dx = sum(bin(r).count('1') - 1 for r in rows)
    L, nn = matriz_reducao(f); cx = conta_xor(L, nn)[0]
    ok = irredutivel(f) and check(b, c, P, out) and len(P.gates) == 40 and dx == 54 and cx == 44
    report('Example 9 (f_{6,5}: irreducible, 40 XORs, dXOR 54, CX 44)', ok,
           f'irreducible={irredutivel(f)}, gates={len(P.gates)}, dXOR={dx}, CX={cx}')

if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--mmax', type=int, default=120)
    a = ap.parse_args()
    check_prop2(a.mmax)
    check_lemma3(min(a.mmax, 200))
    check_thm5(a.mmax)
    check_thm6_prop7(a.mmax)
    check_cor10_cor8(min(a.mmax, 300))
    check_example9()
    fails = [n for n, ok in RESULTS if not ok]
    print(f"\n{len(RESULTS) - len(fails)}/{len(RESULTS)} checks passed" + (f"; FAILED: {fails}" if fails else ''))
    sys.exit(1 if fails else 0)
