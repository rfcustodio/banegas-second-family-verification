#!/usr/bin/env python3
"""Checks added in v22 in response to the review.

1. Lemma (elimination of the low inputs): every row of R' is nonzero,
   for all members with 4 <= m <= MMAX.
2. Reciprocal identity (eq:recip): (f*)^{-1} = (1+y^c)/(1+y^{3c}) + y^{b+c}
   mod y^{m-1}, for all members with m <= 200, and the quotient read from it
   equals the quotient of the division, for random dividends.
3. Special members at m = 20, 100, 500: strip bound 7m/4-1 versus 2m-2, and
   existence of an irreducible trinomial in each of the 15 degrees of Table 8.
4. Word-level doubling steps nu versus ceil(log2(m/c)) (Zhou and Zhang).
Usage: python3 checks/review_checks.py [MMAX]   (default 1100; the quick checks use 300)
"""
import math, random, sys
MMAX = int(sys.argv[1]) if len(sys.argv) > 1 else 1100

def members(lo, hi):
    for m in range(lo, hi + 1):
        for c in range(1, m):
            b = m - 2 * c
            if b <= c:
                break
            yield m, b, c

def pmod(a, f):
    df = f.bit_length() - 1
    while a and a.bit_length() - 1 >= df:
        a ^= f << (a.bit_length() - 1 - df)
    return a

def pmul(a, b):
    r = 0
    while b:
        if b & 1:
            r ^= a
        b >>= 1; a <<= 1
    return r

def pdivmod(a, f):
    q = 0; df = f.bit_length() - 1
    while a and a.bit_length() - 1 >= df:
        s = a.bit_length() - 1 - df
        q |= 1 << s; a ^= f << s
    return q, a

def irreducible(f):
    m = f.bit_length() - 1
    t = 2; pw = [2]
    for _ in range(m):
        t = pmod(pmul(t, t), f); pw.append(t)
    if pw[m] != 2:
        return False
    p, n, ps = 2, m, []
    while p * p <= n:
        if n % p == 0:
            ps.append(p)
            while n % p == 0: n //= p
        p += 1
    if n > 1: ps.append(n)
    for p in ps:
        a, b = f, pw[m // p] ^ 2
        while b: a, b = b, pmod(a, b)
        if a != 1:
            return False
    return True

def rev(p, k):
    return int(format(p, '0%db' % (k + 1))[::-1], 2)

ok = True
# 1. nonzero rows
tot = bad = 0
for m, b, c in members(4, MMAX):
    full, top = (1 << m) - 1, 1 << m
    low = (1 << (b + c)) | (1 << b) | (1 << c) | 1
    v = acc = low
    for _ in range(1, m - 1):
        v <<= 1
        if v & top: v ^= top | low
        acc |= v
        if acc == full: break
    tot += 1
    bad += acc != full
print(f"[1] members 4<=m<={MMAX}: {tot}; with a zero row of R': {bad}")
ok &= bad == 0

# 2. reciprocal identity and quotient
fails = 0; random.seed(1)
for m, b, c in members(5, 200):
    k = m - 1; mask = (1 << k) - 1
    fs = 1 | (1 << c) | (1 << 2 * c) | (1 << (b + c)) | (1 << m)
    s = 0; t = 0
    while 3 * c * t < k:
        s |= 1 << (3 * c * t); t += 1
    s = pmul(s, 1 | (1 << c)) & mask
    if b + c < k: s ^= 1 << (b + c)
    if pmul(s, fs) & mask != 1: fails += 1; continue
    f = (1 << m) | (1 << (b + c)) | (1 << b) | (1 << c) | 1
    n = m - 2
    for _ in range(3):
        D = random.getrandbits(2 * m - 1)
        Q, _r = pdivmod(D, f)
        H = D >> m
        Qs = pmul(rev(H, n), s) & mask
        if rev(Qs, n) != Q: fails += 1
print(f"[2] reciprocal identity and quotient, m<=200: failures {fails}")
ok &= fails == 0

# 3. special members versus trinomials
degs = [5, 6, 18, 20, 42, 54, 100, 126, 155, 162, 294, 378, 486, 500, 882]
notri = [m for m in degs if not any(irreducible((1 << m) | (1 << k) | 1)
                                    for k in range(1, m // 2 + 1))]
print(f"[3] degrees of Table 8 without irreducible trinomial: {notri}")
for m in (20, 100, 500):
    print(f"    m={m}: 7m/4-1={7*m//4-1}  2m-2={2*m-2}")
ok &= not notri and all(7 * m // 4 - 1 < 2 * m - 2 for m in (20, 100, 500))

# 4. doubling steps versus feedback stages
from collections import Counter
cnt = Counter()
for m, b, c in members(5, MMAX):
    n = m - 2
    nu = 0 if 3 * c > n else math.ceil(math.log2((n + 1) / (3 * c)))
    cnt[math.ceil(math.log2(m / c)) - nu] += 1
print(f"[4] ceil(log2(m/c)) - nu over members 5<=m<={MMAX}: {dict(sorted(cnt.items()))}")
ok &= set(cnt) <= {1, 2}
print("ALL OK" if ok else "FAILURE")
sys.exit(0 if ok else 1)
