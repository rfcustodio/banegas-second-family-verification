"""Low-depth variant of Algorithm 1 (Proposition 11): the chain of comb sums is replaced
by the doubling of Corollary 10.  Same symbolic representation and verification as
fam2.py.

Usage:
  python3 generator/lowdepth.py b c        # one member
  python3 generator/lowdepth.py --all 260  # all members with m < 260, checks Prop. 11
"""
import sys
from fam2 import Prog, reduction_rows


def program_lowdepth(b, c):
    m = b + 2 * c; n = m - 2; P = Prog(2 * m - 1)
    h = lambda s: (1 << (m + s)) if 0 <= s <= n else 0
    C = {t: h(t) for t in range(n + 1)}
    s = 3 * c
    while s <= n:                                   # doubling steps
        C = {t: (P.x(C[t], C[t + s]) if t + s <= n else C[t]) for t in range(n + 1)}
        s *= 2
    Cg = lambda t: C.get(t, 0)

    def add(*fs):
        fs = [f for f in fs if f]; acc = fs[0]
        for f in fs[1:]: acc = P.x(acc, f)
        return acc
    Z = {i: add(Cg(i), h(i + b + c)) for i in range(c - 1)}
    U = {}
    for i in range(m):
        if i < c:
            U[i] = add(Z[i], Cg(i + c)) if i in Z else add(Cg(i), Cg(i + c), h(i + b + c))
        else:
            k = i - c
            U[i] = add(Z[k], Cg(i + c)) if (k in Z and h(i + b)) else add(Cg(i - c), Cg(i + c), h(i + b))
    out = [add(1 << i, U[i], U[i - b] if i >= b else 0) for i in range(m)]
    return P, out


def doubling_steps(b, c):
    n = b + 2 * c - 2; s, k = 3 * c, 0
    while s <= n: k += 1; s *= 2
    return k


def predicted_gates(b, c):
    m = b + 2 * c; n = m - 2; s = doubling_steps(b, c)
    return 3 * m - c - 3 + sum(max(0, n + 1 - 3 * c * 2 ** j) for j in range(1, s))


if __name__ == '__main__':
    if sys.argv[1] == '--all':
        M = int(sys.argv[2]); bad = 0; tot = 0
        for m in range(7, M):
            for c in range(1, m):
                b = m - 2 * c
                if b <= c: continue
                P, out = program_lowdepth(b, c); tot += 1
                ok = out == reduction_rows(m, [b + c, b, c])
                d = max(P.depth[o] for o in out)
                if not ok or len(P.gates) > predicted_gates(b, c) or d > doubling_steps(b, c) + 4:
                    bad += 1; print('VIOLATION', m, b, c, ok, len(P.gates), d)
        print(f'Proposition 11: {tot} members with m < {M}, violations: {bad}')
    else:
        b, c = int(sys.argv[1]), int(sys.argv[2]); m = b + 2 * c
        P, out = program_lowdepth(b, c)
        print(f'b={b} c={c} m={m}: {len(P.gates)} XORs (bound {predicted_gates(b, c)}), '
              f'depth {max(P.depth[o] for o in out)} (bound {doubling_steps(b, c) + 4}), '
              f'correct={out == reduction_rows(m, [b + c, b, c])}')
