"""Exact SLP decision: is there an XOR program with k gates computing all rows of R_f?
usage: python3 sat.py m a [b c] k
"""
import sys, time
from pysat.solvers import Solver
from pysat.card import CardEnc, EncType
from pysat.formula import IDPool
from smallm import rows_of

def slp_sat(targets, n, k):
    targets = sorted(set(t for t in targets if bin(t).count('1') >= 2))
    pool = IDPool(); cl = []
    V = {(i, j): pool.id(('g', i, j)) for i in range(k) for j in range(n)}
    for i in range(k):
        ns = n + i
        A = [pool.id(('a', i, p)) for p in range(ns)]; B = [pool.id(('b', i, p)) for p in range(ns)]
        cl += CardEnc.equals(A, 1, vpool=pool, encoding=EncType.seqcounter).clauses
        cl += CardEnc.equals(B, 1, vpool=pool, encoding=EncType.seqcounter).clauses
        for p in range(ns):
            for q in range(p + 1): cl.append([-A[p], -B[q]])       # a < b
        for j in range(n):
            u = pool.id(('u', i, j)); w = pool.id(('w', i, j)); g = V[(i, j)]
            for p in range(ns):
                for sel, x in ((A[p], u), (B[p], w)):
                    if p < n: cl.append([-sel, x if p == j else -x])
                    else:
                        val = V[(p - n, j)]; cl.append([-sel, -x, val]); cl.append([-sel, x, -val])
            cl += [[-g, u, w], [-g, -u, -w], [g, -u, w], [g, u, -w]]
        # symmetry breaking: every gate except the last is used later or is a target (weak)
    for t in targets:
        O = [pool.id(('o', t, i)) for i in range(k)]; cl.append(O)
        for i in range(k):
            for j in range(n): cl.append([-O[i], V[(i, j)] if (t >> j) & 1 else -V[(i, j)]])
    with Solver(name='cadical153', bootstrap_with=cl) as s:
        return s.solve()

if __name__ == '__main__':
    ex = [int(x) for x in sys.argv[1:]]; k = ex.pop()
    f = sum(1 << e for e in ex) | 1
    rows, n = rows_of(f)
    t0 = time.time(); r = slp_sat(rows, n, k)
    print(ex, 'k=%d' % k, 'SAT' if r else 'UNSAT', '%.1fs' % (time.time() - t0), flush=True)
