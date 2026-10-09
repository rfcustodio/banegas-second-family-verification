"""Small-degree study: Paar greedy (deterministic, all tie-breaks), Boyar-Peralta
(with cancellation), and exact SAT bounds for the reduction matrix of f.
usage: python3 smallm.py m a [b c] [bp_runs]
"""
import sys, itertools, random, time
import numpy as np

def pmod(a, f):
    df = f.bit_length() - 1
    while a and a.bit_length() - 1 >= df:
        a ^= f << (a.bit_length() - 1 - df)
    return a

def rows_of(f):
    m = f.bit_length() - 1; n = 2 * m - 1
    cols = [pmod(1 << j, f) for j in range(n)]
    return [sum(1 << j for j in range(n) if (cols[j] >> i) & 1) for i in range(m)], n

# ---------- Paar greedy: deterministic and exhaustive over ties ----------
def paar_step_pairs(R):
    cnt = {}
    for r in R:
        for p in itertools.combinations(sorted(r), 2):
            cnt[p] = cnt.get(p, 0) + 1
    if not cnt: return 1, []
    b = max(cnt.values())
    return b, sorted(p for p, c in cnt.items() if c == b)

def apply(R, p, w):
    out = []
    for r in R:
        if p[0] in r and p[1] in r:
            r = (r - {p[0], p[1]}) | {w}
        out.append(r)
    return out

def paar_det(rows, n):
    R = [frozenset(j for j in range(n) if r >> j & 1) for r in rows]
    w = n; t = 0
    while True:
        b, ps = paar_step_pairs(R)
        if b < 2: break
        R = apply(R, ps[0], w); w += 1; t += 1
    return t + sum(len(r) - 1 for r in R)

def paar_all(rows, n, limit=2_000_000):
    """min over all tie-breaking sequences (Paar's exhaustive variant); memo on canonical state"""
    R0 = [frozenset(j for j in range(n) if r >> j & 1) for r in rows]
    best = [10 ** 9]; seen = {}; nodes = [0]
    def canon(R):  # relabel temporaries by their definition is implicit: use tuple of sorted rows
        return tuple(sorted(tuple(sorted(r)) for r in R))
    def rec(R, w, t):
        nodes[0] += 1
        if nodes[0] > limit: return
        key = canon(R)
        if key in seen and seen[key] <= t: return
        seen[key] = t
        b, ps = paar_step_pairs(R)
        if b < 2:
            c = t + sum(len(r) - 1 for r in R)
            best[0] = min(best[0], c); return
        for p in ps:
            rec(apply(R, p, w), w + 1, t + 1)
    rec(R0, n, 0)
    return best[0], nodes[0] <= limit

# ---------- Boyar-Peralta (SEA 2010), exact distances by BFS, random ties ----------
def bp(targets, n, rng):
    T = sorted(set(t for t in targets if bin(t).count('1') >= 2))
    base = [1 << j for j in range(n)]; gates = []
    N = 1 << n
    while True:
        Bset = set(base); rem = [t for t in T if t not in Bset]
        if not rem: break
        need = max(bin(t).count('1') for t in rem) + 1
        c = np.full(N, 255, dtype=np.uint8); c[0] = 0
        B = np.array(base, dtype=np.int64); front = np.array([0], dtype=np.int64); lev = 0
        while lev < need and front.size:
            nb = np.unique((front[:, None] ^ B[None, :]).ravel()); nb = nb[c[nb] == 255]
            c[nb] = lev + 1; front = nb; lev += 1
        D = np.array([int(c[t]) - 1 for t in rem]); remA = np.array(rem, dtype=np.int64)
        bestkey = None; cands = []
        L = len(base); barr = np.array(base, dtype=np.int64)
        for i in range(L):
            for jj, sv in enumerate(barr[i] ^ barr[i + 1:]):
                sv = int(sv)
                if sv in Bset or sv == 0: continue
                nd = np.minimum(D, c[remA ^ sv].astype(np.int64))
                nd[remA == sv] = 0
                key = (-int(nd.sum()), int((nd * nd).sum()))
                if bestkey is None or key > bestkey: bestkey = key; cands = [(i, i + 1 + jj, sv)]
                elif key == bestkey: cands.append((i, i + 1 + jj, sv))
        i, j, sv = rng.choice(cands); gates.append((i, j)); base.append(sv)
    return gates

def check(gates, targets, n):
    val = [1 << j for j in range(n)]
    for a, b in gates: val.append(val[a] ^ val[b])
    S = set(val); return all(t in S for t in targets)

def show(gates, n, names=None):
    names = names or ['d%d' % j for j in range(n)]
    val = [1 << j for j in range(n)]; out = []
    for i, (a, b) in enumerate(gates):
        v = val[a] ^ val[b]; val.append(v); nm = 't%d' % (i + 1); names = names + [nm]
        canc = bool(val[a] & val[b])
        out.append((nm, names[a], names[b], sorted(j for j in range(n) if v >> j & 1), canc))
    return out

if __name__ == '__main__':
    ex = [int(x) for x in sys.argv[1:]]
    runs = 30
    if len(ex) in (3, 5): runs = ex.pop()
    f = sum(1 << e for e in ex) | 1
    rows, n = rows_of(f)
    dx = sum(bin(r).count('1') - 1 for r in rows)
    pd = paar_det(rows, n)
    pa, complete = paar_all(rows, n)
    best = None; t0 = time.time()
    for s in range(runs):
        g = bp(rows, n, random.Random(s)); assert check(g, rows, n)
        if best is None or len(g) < len(best): best = g
    print(ex, 'dXOR', dx, 'Paar', pd, 'PaarAll', pa, 'complete' if complete else 'partial', 'BP', len(best), '%.0fs' % (time.time() - t0), flush=True)
    import json
    json.dump({'f': ex, 'gates': best, 'n': n}, open('bp_%s.json' % '_'.join(map(str, ex)), 'w'))
