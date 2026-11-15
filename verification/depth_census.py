#!/usr/bin/env python3
"""Area and depth of explicit reduction circuits of the two Banegas families (Section IX-F,
Table 11).

For every irreducible member with m <= 1100 the script builds the circuits below as
straight-line programs of two-input XOR gates, checks every output symbolically against the
reduction matrix (so for all inputs) and records the number of gates and the XOR depth
(longest path from an input d_j to an output r_i).

  second family   A1  Algorithm 1 (Theorem 8)
                  A2  Algorithm 2, chain construction (Theorem 13)
                  LD  low-depth variant of Algorithm 1 (Proposition 17)
                  ST  strip programs of Table 2 for special members (Proposition 4),
                      read from sat/programs.json (fewest gates, depth not optimized)
                  SG  strip programs found by the greedy search of strips.py (best of the
                      lexicographic run and 20 seeded runs by gates, then depth); the terms
                      of each output are added pairing the shallowest signals first
  first family    BCP Eq. (14) of Banegas, Custodio and Panario (2019), b != 2c: 3m-2 gates
                  SP  special case b = 2c: 12m/5-1 gates

Writes depth_members.csv (one line per circuit) and depth_census.csv (one line per degree)
to the data folder and prints the figures quoted in the paper.
Standard library only; about 4 minutes.  Usage: python3 depth_census.py [MMAX]
"""
import csv, json, math, os, re, sys
from collections import Counter, defaultdict

here = os.path.dirname(os.path.abspath(__file__))
for d in ('..', '../algoritmo2', '../generator', '../algorithm2'):
    sys.path.insert(0, os.path.join(here, d))
DATA = next(p for p in (os.path.join(here, '..', '..', 'dados'), os.path.join(here, '..', 'data'))
            if os.path.isdir(p))
from fam2 import program as alg1, reduction_rows
from alg2prog import program as alg2
from lowdepth import program_lowdepth
import strips

MMAX = int(sys.argv[1]) if len(sys.argv) > 1 else 1100


def load(name):
    return [tuple(map(int, l.split())) for l in open(os.path.join(DATA, name))
            if l.strip() and not l.startswith('#') and int(l.split()[0]) <= MMAX]


class SLP:
    """XOR straight-line program over the inputs d_0..d_{n-1}; signals are bitmasks."""
    def __init__(self, n):
        self.val = [1 << j for j in range(n)]; self.dep = [0] * n; self.gates = 0
    def x(self, u, v):
        self.val.append(self.val[u] ^ self.val[v]); self.dep.append(max(self.dep[u], self.dep[v]) + 1)
        self.gates += 1; return len(self.val) - 1
    def result(self, out, rows):
        assert [self.val[o] for o in out] == rows, "symbolic check failed"
        return self.gates, max(self.dep[o] for o in out)


# ---------------------------------------------------------------- second family
def f2_alg1(b, c):
    P, out = alg1(b, c); m = b + 2 * c
    assert out == reduction_rows(m, [b + c, b, c])
    return len(P.gates), max(P.depth[o] for o in out)

def f2_lowdepth(b, c):
    P, out = program_lowdepth(b, c); m = b + 2 * c
    assert out == reduction_rows(m, [b + c, b, c])
    return len(P.gates), max(P.depth[o] for o in out)

def f2_alg2(b, c):
    prog, val, dep, m = alg2(b, c)
    assert [val[('r', i)] for i in range(m)] == reduction_rows(m, [b + c, b, c])
    return len(prog), max(dep[('r', i)] for i in range(m))

STRIPS = json.load(open(os.path.join(DATA, 'sat', 'programs.json')))
BASE = [(2, 1), (3, 1), (4, 1), (5, 1), (3, 2)]

def f2_strips(b, c):
    """f = G(x^g) with G = f_{b/g,c/g} a base polynomial: strip r (0 <= r < g) reduces the
    coefficients d_{r+g*t} modulo G; strips 0..g-2 have 2k inputs (program R1), the last
    one has 2k-1 (program R2)."""
    g = math.gcd(b, c); bp, cp = b // g, c // g
    if (bp, cp) not in BASE: return None
    k = bp + 2 * cp; m = g * k
    P = SLP(2 * m - 1); out = [None] * m
    for r in range(g):
        prog = STRIPS[('R1_' if r < g - 1 else '') + f'f_{bp}_{cp}']
        name = {}
        for line in prog['gates'] + prog['outputs']:
            lhs, u, v = re.fullmatch(r"(\w+) = (\w+) \^ (\w+)", line).groups()
            idx = lambda s: r + g * int(s[1:]) if s[0] == 'd' else name[s]
            name[lhs] = P.x(idx(u), idx(v))
        for i in range(k): out[r + g * i] = name[f'r{i}']
    return P.result(out, reduction_rows(m, [b + c, b, c]))


def greedy_into(P, prog, r, g):
    """Adds the greedy strip program prog = (gates, rows) to P on the inputs r + g*t."""
    gates, rows = prog; name = {}
    idx = lambda v: name[v] if v >= strips.TMP else r + g * v
    for t, u, v in gates: name[t] = P.x(idx(u), idx(v))
    out = []
    for row in rows:
        row = [idx(v) for v in row]
        while len(row) > 1:
            row.sort(key=lambda t: (P.dep[t], t))
            row.append(P.x(row.pop(0), row.pop(0)))
        out.append(row[0])
    return out

GREEDY = {}
def greedy_pair(bp, cp):
    if (bp, cp) not in GREEDY:
        k = bp + 2 * cp; pair = []
        for top in (2 * k - 1, 2 * k - 2):                     # R1 strip, R2 strip
            rows = strips.rows_of(strips.fam(bp, cp), top); cands = []
            for seed in [None] + list(range(20)):
                prog = strips.greedy(rows, seed); P = SLP(top + 1); out = greedy_into(P, prog, 0, 1)
                cands.append((P.gates, max(P.dep[o] for o in out), len(cands), prog))
            pair.append(min(cands)[3])
        GREEDY[bp, cp] = pair
    return GREEDY[bp, cp]

def f2_strips_greedy(b, c):
    g = math.gcd(b, c); bp, cp = b // g, c // g
    if (bp, cp) not in BASE: return None
    k = bp + 2 * cp; m = g * k; P1, P2 = greedy_pair(bp, cp)
    P = SLP(2 * m - 1); out = [None] * m
    for r in range(g):
        for i, o in enumerate(greedy_into(P, P1 if r < g - 1 else P2, r, g)): out[r + g * i] = o
    return P.result(out, reduction_rows(m, [b + c, b, c]))


# ---------------------------------------------------------------- first family
def f1_bcp(b, c):
    """Eq. (14) of BCP 2019 for x^{2b+c}+x^{b+c}+x^b+x^c+1, b != 2c: the b-1 sums
    T1 = d_{i+2b+c}+d_{i+3b+2c} are shared by three outputs; the remaining terms of each
    output are added pairing the shallowest signals first."""
    m = 2 * b + c; P = SLP(2 * m - 1); rows = [[i] for i in range(m)]
    for i in range(b - 1):
        t = P.x(i + 2 * b + c, i + 3 * b + 2 * c)
        for j in (0, b, b + c): rows[i + j].append(t)
    for j in (b - 1, b + c - 1, 2 * b - 1, 2 * b + c - 1): rows[j].append(3 * b + c - 1)
    for i in range(c):
        for j in (0, c, 2 * b): rows[i + j].append(i + 3 * b + c)
    for i in range(b - 1):
        rows[i + c].append(i + 2 * b + c); rows[i + 2 * c].append(i + 3 * b + 2 * c)
    out = []
    for row in rows:
        while len(row) > 1:
            row.sort(key=lambda t: (P.dep[t], t))
            row.append(P.x(row.pop(0), row.pop(0)))
        out.append(row[0])
    return P.result(out, reduction_rows(m, [b + c, b, c]))

def f1_special(c):
    """b = 2c, f = x^{5c}+x^{3c}+x^{2c}+x^c+1: per residue j mod c, with a_k = d_{j+kc},
    12 gates (11 for j = c-1, where a_9 does not exist)."""
    m = 5 * c; P = SLP(2 * m - 1); out = [None] * m
    for j in range(c):
        a = lambda k: j + k * c
        t = P.x(a(5), a(6)); u = P.x(a(7), a(9)) if j < c - 1 else a(7)
        ys = (P.x(P.x(a(0), a(8)), P.x(a(5), a(7))), P.x(a(1), P.x(t, u)), P.x(a(2), t),
              P.x(a(3), P.x(t, a(8))), P.x(a(4), P.x(a(6), u)))
        for k, y in enumerate(ys): out[j + k * c] = y
    return P.result(out, reduction_rows(m, [3 * c, 2 * c, c]))


# ---------------------------------------------------------------- census
members = []                                   # (m, family, b, c, construction, gates, depth)
for m, b, c in load('fam2_irr.txt'):
    g1 = f2_alg1(b, c); g2 = f2_alg2(b, c); gl = f2_lowdepth(b, c); gs = f2_strips(b, c)
    N = c * ((b + c) // (3 * c)) + max(0, (b + c) % (3 * c) - 2 * c)
    assert g1[0] <= 3 * m - c - 3 and g2[0] == 3 * m - 3 - N
    members += [(m, 2, b, c, 'A1', *g1), (m, 2, b, c, 'A2', *g2), (m, 2, b, c, 'LD', *gl)]
    if gs: members += [(m, 2, b, c, 'ST', *gs), (m, 2, b, c, 'SG', *f2_strips_greedy(b, c))]
for m, b, c in load('fam1_irr.txt'):
    if b == 2 * c:
        g = f1_special(c); assert g[0] == 12 * m // 5 - 1
        members.append((m, 1, b, c, 'SP', *g))
    else:
        g = f1_bcp(b, c); assert g[0] == 3 * m - 2
        members.append((m, 1, b, c, 'BCP', *g))
with open(os.path.join(DATA, 'depth_members.csv'), 'w', newline='') as fh:
    w = csv.writer(fh); w.writerow('m family b c construction gates depth'.split()); w.writerows(members)

F = {1: defaultdict(list), 2: defaultdict(list)}
for m, fam, b, c, con, gates, depth in members: F[fam][m].append((gates, depth, b, c, con))
BUDGETS = (3, 4, 5, 6, 8, 12)
rows = []
for m in sorted(F[2]):
    c2 = F[2][m]; c1 = F[1].get(m)
    ga = min(c2); dm = min(x[1] for x in c2); gd = min(x for x in c2 if x[1] == dm)
    row = dict(m=m, f2_min_gates=ga[0], f2_depth_at_min_gates=ga[1], f2_min_depth=dm, f2_gates_at_min_depth=gd[0],
               f1_min_gates=min(c1)[0] if c1 else '', f1_min_depth=min(x[1] for x in c1) if c1 else '')
    for D in BUDGETS:
        xs = [x[0] for x in c2 if x[1] <= D]; row[f'f2_min_gates_depth_le_{D}'] = min(xs) if xs else ''
    rows.append(row)
with open(os.path.join(DATA, 'depth_census.csv'), 'w', newline='') as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)

n2 = sum(1 for x in members if x[1] == 2); n1 = len(members) - n2
print(f"circuits built and checked symbolically: {n2} (second family, {len(load('fam2_irr.txt'))} members), "
      f"{n1} (first family)")
print("first family: depth of all circuits:", sorted(Counter(x[6] for x in members if x[1] == 1).items()))
print("strip programs of special members (m, b, c, construction, gates, depth):",
      [(x[0], x[2], x[3], x[4], x[5], x[6]) for x in members if x[4] in ('ST', 'SG')])
S = [r for r in rows if r['f1_min_gates'] != '']
print(f"degrees with irreducible members of both families: {len(S)}")
print("  first family, minimum depth:", sorted(Counter(r['f1_min_depth'] for r in S).items()))
print("  second family, minimum depth:", sorted(Counter(r['f2_min_depth'] for r in S).items()))
dd = sorted(r['f2_depth_at_min_gates'] for r in S)
print(f"  second family, depth of the circuit with fewest gates: 3 in {dd.count(3)}, 4 in {dd.count(4)}, "
      f"5 to 8 in {sum(5 <= d <= 8 for d in dd)}, more than 8 in {sum(d > 8 for d in dd)} degrees; "
      f"median {dd[len(dd)//2]}, maximum {dd[-1]}")
sv = [100 * (r['f1_min_gates'] - r['f2_min_gates']) / r['f1_min_gates'] for r in S]
print(f"  no depth limit: second family has fewer gates in {sum(s > 0 for s in sv)} degrees, mean saving {sum(sv)/len(sv):.2f}%")
for D in BUDGETS:
    T = [r for r in S if r[f'f2_min_gates_depth_le_{D}'] != '']
    sv = [100 * (r['f1_min_gates'] - r[f'f2_min_gates_depth_le_{D}']) / r['f1_min_gates'] for r in T]
    ex = [100 * (r[f'f2_min_gates_depth_le_{D}'] - r['f2_min_gates']) / r['f2_min_gates'] for r in T]
    pos = [s for s in sv if s > 0]
    print(f"  depth <= {D:2d}: second family has a circuit in {len(T):3d} degrees, fewer gates than the first in "
          f"{len(pos):3d} (mean saving in these {sum(pos)/len(pos):5.2f}%, in all {sum(sv)/len(sv):5.2f}%, "
          f"min {min(sv):7.2f}%, max {max(sv):5.2f}%); gates above its own minimum: mean {sum(ex)/len(ex):.2f}%, "
          f"max {max(ex):.2f}%")
for m in (5, 155, 163, 228, 571):
    if m in F[2]:
        front = sorted(x for x in F[2][m] if not any((y[0] <= x[0] and y[1] <= x[1] and y[:2] != x[:2]) for y in F[2][m]))
        seen = set(); front = [x for x in front if not (x[:2] in seen or seen.add(x[:2]))]
        print(f"m = {m}: second family, nondominated (gates, depth, b, c, construction): {front};"
              f" first family: {sorted(F[1][m])[:1] if m in F[1] else 'none'}")
