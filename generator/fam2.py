"""Closed-form reduction program for f = x^{b+2c} + x^{b+c} + x^b + x^c + 1  (b > c >= 1).

Signals are GF(2)-linear forms in the product coefficients d_0..d_{2m-2}, stored as int
bitmasks; a program is correct iff every output form equals the corresponding row of the
reduction matrix, which implies correctness for all inputs.

Program (n = m-2, h_s = d_{m+s}):
  C_t  = h_t + C_{t+3c}                       (comb sums, t = n-3c ... 0)
  Z_i  = C_i + h_{i+b+c}                      (0 <= i <= c-2)
  U_i  = Z_i + C_{i+c}                        (0 <= i <= c-2)
  U_{c-1} = C_{c-1} + C_{2c-1}
  U_i  = Z_{i-c} + C_{i+c}                    (c <= i <= 2c-2)
  U_i  = C_{i-c} + C_{i+c}                    (2c-1 <= i <= b+c-2)
  U_i  = C_{i-c}                              (b+c-1 <= i <= m-1)
  r_i  = d_i + U_i (+ U_{i-b} if i >= b)
"""
import sys

def reduction_rows(m, exps):
    f = (1 << m) | sum(1 << e for e in exps) | 1
    n = 2 * m - 1
    rows = [0] * m
    col = 1
    for j in range(n):
        t, i = col, 0
        while t:
            if t & 1: rows[i] |= 1 << j
            t >>= 1; i += 1
        col <<= 1
        if col >> m & 1: col ^= f
    return rows

class Prog:
    def __init__(self, n):
        self.gates = []; self.have = {1 << j for j in range(n)}; self.depth = {1 << j: 0 for j in range(n)}
    def x(self, u, v):
        assert u in self.have and v in self.have and u != v
        w = u ^ v
        if w not in self.have:
            self.have.add(w); self.gates.append((u, v)); self.depth[w] = max(self.depth[u], self.depth[v]) + 1
        return w

def program(b, c, share_Z=True):
    m = b + 2 * c; n = m - 2
    P = Prog(2 * m - 1)
    h = lambda s: (1 << (m + s)) if 0 <= s <= n else 0
    C = {}
    for t in range(n, -1, -1):                     # comb sums along stride 3c
        C[t] = h(t) if t + 3 * c > n else P.x(h(t), C[t + 3 * c])
    Cg = lambda t: C.get(t, 0)
    def add(*forms):
        forms = [f for f in forms if f]
        acc = forms[0]
        for f in forms[1:]: acc = P.x(acc, f)
        return acc
    Z = {}
    for i in range(c - 1):
        Z[i] = add(Cg(i), h(i + b + c)) if share_Z else None
    U = {}
    for i in range(m):
        if i < c:
            U[i] = add(Z[i], Cg(i + c)) if (share_Z and i in Z) else add(Cg(i), Cg(i + c), h(i + b + c))
        else:
            k = i - c
            if share_Z and k in Z and h(i + b):   # U_i = C_{i-c} + C_{i+c} + h_{i+b} = Z_{i-c} + C_{i+c}
                U[i] = add(Z[k], Cg(i + c))
            else:
                U[i] = add(Cg(i - c), Cg(i + c), h(i + b))
    out = []
    for i in range(m):
        out.append(add(1 << i, U[i], U[i - b] if i >= b else 0))
    return P, out

def check(b, c, P, out):
    m = b + 2 * c
    return out == reduction_rows(m, [b + c, b, c])

if __name__ == '__main__':
    b, c = int(sys.argv[1]), int(sys.argv[2])
    m = b + 2 * c
    P, out = program(b, c)
    print(f"b={b} c={c} m={m}: {len(P.gates)} XORs, depth {max(P.depth[o] for o in out)}, "
          f"correct={check(b, c, P, out)}, 3m-c-3={3*m-c-3}")
