"""Exact decision: does a linear straight-line program with K XOR gates compute the
given targets? Targets are bitmasks over n inputs. Targets of weight <= 1 and duplicates
need no gate. Encoding: each gate selects two distinct earlier signals (one-hot A, B with
A < B); its value bits are the XOR of the selected signals; each target equals some gate."""
import sys, itertools, time
from pysat.formula import IDPool
from pysat.card import CardEnc, EncType
from pysat.solvers import Cadical153

def encode(targets, n, K):
    """CNF for 'a program with K XOR gates computes the targets'. Returns (clauses,
    pool, T), with T the sorted distinct targets of weight >= 2. Variables: ('a',i,p) and
    ('b',i,p) select the operands of gate i among the n inputs and the earlier gates
    (p < n + i, A index < B index); ('x',i,t) is bit t of the value of gate i;
    ('o',j,i) says that target j is gate i."""
    T = sorted({t for t in targets if bin(t).count('1') >= 2})
    pool = IDPool(); cl = []
    X = lambda i, t: pool.id(('x', i, t))
    A = lambda i, p: pool.id(('a', i, p))
    B = lambda i, p: pool.id(('b', i, p))
    for i in range(K):
        S = n + i
        for sel in (A, B):
            lits = [sel(i, p) for p in range(S)]
            cl += CardEnc.equals(lits=lits, bound=1, vpool=pool, encoding=EncType.seqcounter).clauses
        # A index < B index
        for p in range(S):
            for q in range(0, p + 1):
                cl.append([-A(i, p), -B(i, q)])
        for t in range(n):
            ya = pool.id(('ya', i, t)); yb = pool.id(('yb', i, t))
            for p in range(S):
                if p < n:
                    val = 1 if p == t else 0
                    for sel, y in ((A, ya), (B, yb)):
                        cl.append([-sel(i, p), y if val else -y])
                else:
                    g = p - n
                    for sel, y in ((A, ya), (B, yb)):
                        cl.append([-sel(i, p), -X(g, t), y]); cl.append([-sel(i, p), X(g, t), -y])
            x = X(i, t)
            cl += [[-x, ya, yb], [-x, -ya, -yb], [x, -ya, yb], [x, ya, -yb]]
    for j, tv in enumerate(T):
        os_ = [pool.id(('o', j, i)) for i in range(K)]
        cl.append(os_)
        for i in range(K):
            for t in range(n):
                cl.append([-os_[i], X(i, t) if (tv >> t) & 1 else -X(i, t)])
    return cl, pool, T

def decode(model, pool, n, K):
    """Operand pairs (p, q) of the K gates from a satisfying assignment."""
    pos = set(l for l in model if l > 0); prog = []
    for i in range(K):
        S = n + i
        pa = [p for p in range(S) if pool.id(('a', i, p)) in pos][0]
        pb = [p for p in range(S) if pool.id(('b', i, p)) in pos][0]
        prog.append((pa, pb))
    return prog

def decide(targets, n, K, timeout=None):
    T = sorted({t for t in targets if bin(t).count('1') >= 2})
    if not T: return True
    if K < len(T): return False
    cl, pool, T = encode(targets, n, K)
    with Cadical153(bootstrap_with=cl) as s:
        return s.solve()

def reduced_targets(m, b, c):
    """rows of R' : outputs minus their low input, over the m-1 high inputs."""
    ex = [b + c, b, c, 0]
    col = [0] * m; col[0] = 1; rows = [0] * m
    for j in range(2 * m - 1):
        if j > 0:
            top = col[m - 1]; col = [0] + col[:-1]
            if top:
                for e in ex: col[e] ^= 1
        if j >= m:
            for i in range(m):
                if col[i]: rows[i] |= 1 << (j - m)
    return rows, m - 1

if __name__ == '__main__':
    m, b, c = map(int, sys.argv[1:4])
    rows, n = reduced_targets(m, b, c)
    closedR = (3 * m - c - 3) - m
    for K in ([int(sys.argv[4])] if len(sys.argv) > 4 else [closedR, closedR - 1]):
        t0 = time.time(); r = decide(rows, n, K)
        print(f"m={m} b={b} c={c}: program with {K} gates for R' (total {K+m}) -> {'SAT' if r else 'UNSAT'} ({time.time()-t0:.1f}s)", flush=True)
