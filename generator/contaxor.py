#!/usr/bin/env python3
"""
contaxor.py  --  numero de XORs da reducao modular em GF(2)[x]/(f) pelo metodo Conta-XOR
                 (Banegas, 2015), que equivale ao algoritmo guloso de Paar (1997).

Etapas:
  1. monta a matriz de reducao R_f (linha i = bits d_j que entram no bit i do resto);
  2. elimina termos repetidos aos pares (feito automaticamente pela aritmetica em GF(2));
  3. enquanto algum par de operandos aparece em 2 ou mais linhas, substitui o par
     mais frequente por uma variavel temporaria (desempate: menor par em ordem
     lexicografica, como no Conta-XOR);
  4. N = (numero de temporarias) + soma(|linha| - 1).

Uso:
  python3 contaxor.py 163 7 6 3 0          # expoentes de f (o termo 0 e opcional)
  python3 contaxor.py 163 7 6 3 -r 50      # tambem 50 rodadas com desempate aleatorio
  python3 contaxor.py 10 4 3 1 -p          # imprime o programa de XORs
  python3 contaxor.py 163 7 6 3 --sem-irred  # nao testa irredutibilidade

Somente biblioteca padrao do Python 3 (testado com 3.8+).
"""
import argparse, random, sys, time
from math import isqrt

# ------------------------------------------------------------------ GF(2)[x]
def pmod(a, f):
    df = f.bit_length() - 1
    while a and a.bit_length() - 1 >= df:
        a ^= f << (a.bit_length() - 1 - df)
    return a

def mulmod(a, b, f):
    r = 0
    while b:
        if b & 1:
            r ^= a
        b >>= 1
        a <<= 1
        if a >> (f.bit_length() - 1) & 1:
            a ^= f
    return r

def pgcd(a, b):
    while b:
        a, b = b, pmod(a, b)
    return a

def fatores_primos(n):
    fs, p = [], 2
    while p * p <= n:
        if n % p == 0:
            fs.append(p)
            while n % p == 0:
                n //= p
        p += 1
    if n > 1:
        fs.append(n)
    return fs

def irredutivel(f):
    """Teste de Rabin: x^(2^m) = x mod f e mdc(x^(2^(m/q)) - x, f) = 1 para todo primo q | m."""
    m = f.bit_length() - 1
    pot = [2]                       # pot[k] = x^(2^k) mod f
    for _ in range(m):
        pot.append(mulmod(pot[-1], pot[-1], f))
    if pot[m] != 2:
        return False
    return all(pgcd(f, pot[m // q] ^ 2) == 1 for q in fatores_primos(m))

# ------------------------------------------------------------------ matriz de reducao
def matriz_reducao(f):
    m = f.bit_length() - 1
    n = 2 * m - 1
    linhas = [set() for _ in range(m)]
    c = 1                            # x^j mod f
    for j in range(n):
        t, i = c, 0
        while t:
            if t & 1:
                linhas[i].add(j)
            t >>= 1
            i += 1
        c <<= 1
        if c >> m & 1:
            c ^= f
    return linhas, n

# ------------------------------------------------------------------ Paar / Conta-XOR
def conta_xor(linhas0, n, rng=None):
    """Retorna (numero de XORs, programa, linhas finais).
    programa: lista de (w, u, v) significando t_w = u XOR v.
    rng=None -> desempate lexicografico (Conta-XOR); caso contrario, aleatorio."""
    linhas = [set(r) for r in linhas0]
    cont = {}                        # par (u,v), u<v -> numero de linhas que o contem
    for i, r in enumerate(linhas):
        l = sorted(r)
        for x in range(len(l)):
            for y in range(x + 1, len(l)):
                p = (l[x], l[y])
                cont[p] = cont.get(p, 0) + 1
    prog, w = [], n
    while True:
        mx = 1
        for c in cont.values():
            if c > mx:
                mx = c
        if mx < 2:
            break
        cand = [p for p, c in cont.items() if c == mx]
        p = min(cand) if rng is None else rng.choice(cand)
        u, v = p
        prog.append((w, u, v))
        for i, r in enumerate(linhas):
            if u in r and v in r:
                # remove os pares que envolvem u ou v nesta linha
                r.discard(u); r.discard(v)
                for b in r:
                    for a in (u, v):
                        q = (a, b) if a < b else (b, a)
                        cont[q] -= 1
                        if cont[q] == 0:
                            del cont[q]
                cont[p] -= 1
                if cont[p] == 0:
                    del cont[p]
                # adiciona os pares com a nova variavel w
                for b in r:
                    q = (b, w)
                    cont[q] = cont.get(q, 0) + 1
                r.add(w)
        w += 1
    total = len(prog) + sum(len(r) - 1 for r in linhas if r)
    return total, prog, linhas

def profundidade(prog, linhas, n):
    dep = {j: 0 for j in range(n)}
    for w, u, v in prog:
        dep[w] = max(dep[u], dep[v]) + 1
    pm = 0
    for r in linhas:
        ds = sorted(dep[x] for x in r)
        while len(ds) > 1:            # combina sempre os dois mais rasos
            a, b = ds.pop(0), ds.pop(0)
            nv = max(a, b) + 1
            k = 0
            while k < len(ds) and ds[k] < nv:
                k += 1
            ds.insert(k, nv)
        pm = max(pm, ds[0] if ds else 0)
    return pm

def verifica(prog, linhas, f, testes=300, rng=random.Random(1)):
    """Executa o programa em entradas aleatorias e compara com a divisao polinomial."""
    m = f.bit_length() - 1
    n = 2 * m - 1
    for _ in range(testes):
        D = rng.getrandbits(n)
        val = {j: (D >> j) & 1 for j in range(n)}
        for w, u, v in prog:
            val[w] = val[u] ^ val[v]
        R = pmod(D, f)
        for i, r in enumerate(linhas):
            s = 0
            for x in r:
                s ^= val[x]
            if s != (R >> i) & 1:
                return False
    return True

# ------------------------------------------------------------------ interface
def nome(j, n):
    return f"d{j}" if j < n else f"t{j - n + 1}"

def main():
    ap = argparse.ArgumentParser(description="Conta-XOR (= guloso de Paar) para a reducao modulo f.")
    ap.add_argument("expoentes", nargs="+", type=int, help="expoentes de f, ex.: 163 7 6 3 0")
    ap.add_argument("-r", "--aleatorio", type=int, default=0, metavar="K",
                    help="alem do Conta-XOR, K rodadas com desempate aleatorio (R-Paar)")
    ap.add_argument("-s", "--semente", type=int, default=1)
    ap.add_argument("-p", "--programa", action="store_true", help="imprime o programa de XORs")
    ap.add_argument("--sem-irred", action="store_true", help="nao testa irredutibilidade")
    a = ap.parse_args()

    ex = sorted(set(a.expoentes) | {0}, reverse=True)
    f = 0
    for e in ex:
        f |= 1 << e
    m = ex[0]
    termos = " + ".join(("1" if e == 0 else "x" if e == 1 else f"x^{e}") for e in ex)
    print(f"f(x) = {termos}   (m = {m}, peso {len(ex)})")
    if not a.sem_irred:
        t0 = time.time()
        irr = irredutivel(f)
        print(f"irredutivel: {'sim' if irr else 'NAO'}  ({time.time() - t0:.2f}s)")

    linhas, n = matriz_reducao(f)
    dx = sum(len(r) - 1 for r in linhas)
    print(f"sem otimizacao (d-XOR): {dx}")

    t0 = time.time()
    total, prog, fin = conta_xor(linhas, n)
    ok = verifica(prog, fin, f)
    print(f"Conta-XOR: {total} XORs  ({len(prog)} temporarias), profundidade {profundidade(prog, fin, n)}"
          f", verificado: {'ok' if ok else 'FALHOU'}  ({time.time() - t0:.2f}s)")

    melhor = (total, prog, fin)
    if a.aleatorio:
        rng = random.Random(a.semente)
        t0 = time.time()
        for _ in range(a.aleatorio):
            r = conta_xor(linhas, n, rng)
            if r[0] < melhor[0]:
                melhor = r
        ok = verifica(melhor[1], melhor[2], f)
        print(f"R-Paar ({a.aleatorio} rodadas aleatorias): {melhor[0]} XORs, profundidade "
              f"{profundidade(melhor[1], melhor[2], n)}, verificado: {'ok' if ok else 'FALHOU'}"
              f"  ({time.time() - t0:.2f}s)")

    if a.programa:
        total, prog, fin = melhor
        print("\n# programa (d_j = coeficiente j do produto, j = 0..2m-2)")
        for w, u, v in prog:
            print(f"{nome(w, n)} = {nome(u, n)} ^ {nome(v, n)}")
        for i, r in enumerate(fin):
            print(f"c{i} = " + " ^ ".join(nome(x, n) for x in sorted(r)))

if __name__ == "__main__":
    main()
