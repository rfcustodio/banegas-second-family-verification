#!/usr/bin/env python3
"""Implementacao independente do Algoritmo 1 do artigo "Banegas' Second Family
of Irreducible Pentanomials" (Tomaszewski & Custodio), pra contracheque pedido
pelo professor.

Nao reusa nenhuma logica do "gerador simbolico" citado no artigo — e' escrita
direto do pseudocodigo (Algoritmo 1, Secao 5) e da Definicao 4 (comb sums),
so' reaproveitando `matriz_reducao` do contaxor.py como ORACULO independente
pra conferir corretude (aquele codigo ja' foi validado à exaustao noutro
contexto, entao serve de "gabarito" pra bater o resultado).

Cada valor intermediario (h_s, C_t, Z_i, U_k, r_i) e' representado por um
frozenset de indices de colunas d_0..d_{2m-2}: o valor e' o XOR de exatamente
esses d_j. Isso permite conferir corretude simbolicamente (sem sortear D) e
contar profundidade junto.
"""
from __future__ import annotations

from dataclasses import dataclass

from contaxor import matriz_reducao


@dataclass
class Circuito:
    r: list[frozenset[int]]   # r[i] = conjunto de d_j cujo XOR da' a saida i
    depth: dict[int, int]     # profundidade de cada r[i] (por indice)
    portas: int               # total de portas XOR realmente emitidas
    profundidade: int         # max(depth.values())


def _xor(vals, depths, a, b):
    """Emite uma porta XOR combinando os valores/rotulos `a` e `b`.
    Retorna (novo_valor, nova_profundidade). Sempre custa 1 porta."""
    return vals[a] ^ vals[b], 1 + max(depths[a], depths[b])


# =============================================================================
# ALGORITMO 1 DO ARTIGO (Secao 5) COMECA AQUI
#
# Pseudocodigo original:
#
#   Input : d_0, ..., d_{2m-2}
#   Output: r_0, ..., r_{m-1} com sum r_i x^i = D mod f_{b,c}
#    1  for t <- n to 0 do                          // comb sums, b-c-1 XORs
#    2      if t+3c <= n then Ct <- ht XOR C_{t+3c};
#    3      else Ct <- ht;
#    4  for i <- 0 to c-2 do                         // shared pairs, c-1 XORs
#    5      Zi <- Ci XOR h_{i+b+c}
#    6  for k <- 0 to m-1 do                         // b+c-1 XORs no total
#    7      if k <= c-2 then
#    8          Uk <- Zk XOR C_{k+c}
#    9      else if k = c-1 then
#   10          Uk <- C_{c-1} XOR C_{2c-1}
#   11      else if k <= 2c-2 then
#   12          Uk <- Z_{k-c} XOR C_{k+c}
#   13      else if k <= b+c-2 then
#   14          Uk <- C_{k-c} XOR C_{k+c}
#   15      else Uk <- C_{k-c};
#   16  for i <- 0 to m-1 do                         // m+(m-b) XORs
#   17      if i >= b then ri <- (di XOR Ui) XOR Ui-b;
#   18      else ri <- di XOR Ui;
#
# As linhas 1-3 (comb sums) sao calculadas em `algoritmo1()` (cadeia) ou em
# `algoritmo1_low_depth()` (dobramento) -- sao as DUAS formas de preencher o
# mesmo array C_val/C_dep que esta funcao recebe pronto. As linhas 4-18 (Z, U,
# r) sao identicas nas duas versoes, por isso ficam compartilhadas aqui.
# =============================================================================

def _completar_com_C(b: int, c: int, C_val: list, C_dep: list, portas: int) -> Circuito:
    """Linhas 4-18 do Algoritmo 1 (Z, U, r), a partir de comb sums C_t ja'
    prontos (index 0..n) -- recebidos de `algoritmo1()` ou `algoritmo1_low_depth()`,
    que diferem so' em COMO os C_t sao computados (linhas 1-3)."""
    m = b + 2 * c
    n = m - 2

    # h_s = d_{m+s}: convencao de entrada dada no cabecalho do Algoritmo 1.
    h_val = [frozenset({m + s}) for s in range(n + 1)]
    h_dep = [0] * (n + 1)

    def h(s):
        return h_val[s], h_dep[s]

    def C(t):
        return C_val[t], C_dep[t]

    # --- linhas 4-5: Zi <- Ci XOR h_{i+b+c}, i = 0..c-2 ---------------------
    Z_val = [None] * max(c - 1, 0)
    Z_dep = [None] * max(c - 1, 0)
    for i in range(0, c - 1):                      # linha 4: for i <- 0 to c-2
        cv, cd = C(i)
        hv, hd = h(i + b + c)
        Z_val[i] = cv ^ hv                          # linha 5: Zi <- Ci XOR h_{i+b+c}
        Z_dep[i] = 1 + max(cd, hd)
        portas += 1

    def Z(i):
        return Z_val[i], Z_dep[i]

    # --- linhas 6-15: Uk, k = 0..m-1 -----------------------------------------
    U_val = [None] * m
    U_dep = [None] * m
    for k in range(m):                              # linha 6: for k <- 0 to m-1
        if k <= c - 2:                              # linha 7: if k <= c-2
            zv, zd = Z(k)
            cv, cd = C(k + c)
            U_val[k] = zv ^ cv                       # linha 8: Uk <- Zk XOR C_{k+c}
            U_dep[k] = 1 + max(zd, cd)
            portas += 1
        elif k == c - 1:                            # linha 9: else if k = c-1
            c1v, c1d = C(c - 1)
            c2v, c2d = C(2 * c - 1)
            U_val[k] = c1v ^ c2v                     # linha 10: Uk <- C_{c-1} XOR C_{2c-1}
            U_dep[k] = 1 + max(c1d, c2d)
            portas += 1
        elif k <= 2 * c - 2:                         # linha 11: else if k <= 2c-2
            zv, zd = Z(k - c)
            cv, cd = C(k + c)
            U_val[k] = zv ^ cv                       # linha 12: Uk <- Z_{k-c} XOR C_{k+c}
            U_dep[k] = 1 + max(zd, cd)
            portas += 1
        elif k <= b + c - 2:                        # linha 13: else if k <= b+c-2
            c1v, c1d = C(k - c)
            c2v, c2d = C(k + c)
            U_val[k] = c1v ^ c2v                     # linha 14: Uk <- C_{k-c} XOR C_{k+c}
            U_dep[k] = 1 + max(c1d, c2d)
            portas += 1
        else:                                       # linha 15: else Uk <- C_{k-c}
            U_val[k], U_dep[k] = C(k - c)            # alias, nao custa porta

    def U(k):
        return U_val[k], U_dep[k]

    # --- linhas 16-18: saidas r_i, i = 0..m-1 --------------------------------
    r = [None] * m
    depth = {}
    for i in range(m):                              # linha 16: for i <- 0 to m-1
        d_i = frozenset({i})
        uv, ud = U(i)
        if i >= b:                                  # linha 17: if i >= b
            ubv, ubd = U(i - b)
            v1 = d_i ^ uv                            # (di XOR Ui) --
            d1 = 1 + max(0, ud)
            portas += 1
            r[i] = v1 ^ ubv                          # -- XOR Ui-b: ri <- (di XOR Ui) XOR Ui-b
            depth[i] = 1 + max(d1, ubd)
            portas += 1
        else:                                       # linha 18: else ri <- di XOR Ui
            r[i] = d_i ^ uv
            depth[i] = 1 + max(0, ud)
            portas += 1

    return Circuito(r=r, depth=depth, portas=portas, profundidade=max(depth.values()))


def algoritmo1(b: int, c: int) -> Circuito:
    """Algoritmo 1 literal (Secao 5), linhas 1-3: comb sums em cadeia serial.
    As linhas 4-18 (identicas pra qualquer forma de calcular os Ct) estao em
    `_completar_com_C`."""
    if not (b > c >= 1):
        raise ValueError("precisa de b > c >= 1")
    m = b + 2 * c
    n = m - 2

    h_val = [frozenset({m + s}) for s in range(n + 1)]
    h_dep = [0] * (n + 1)

    portas = 0
    C_val = [None] * (n + 1)
    C_dep = [None] * (n + 1)
    for t in range(n, -1, -1):                      # linha 1: for t <- n to 0
        hv, hd = h_val[t], h_dep[t]
        if t + 3 * c <= n:                           # linha 2: if t+3c<=n
            cv, cd = C_val[t + 3 * c], C_dep[t + 3 * c]
            C_val[t] = hv ^ cv                       # Ct <- ht XOR C_{t+3c}
            C_dep[t] = 1 + max(hd, cd)
            portas += 1
        else:                                       # linha 3: else Ct <- ht
            C_val[t] = hv          # alias, nao custa porta
            C_dep[t] = hd

    return _completar_com_C(b, c, C_val, C_dep, portas)
# ALGORITMO 1 DO ARTIGO TERMINA AQUI (linhas 1-18 completas: esta funcao +
# `_completar_com_C`). A partir daqui sao as variantes/conferencias.
# =============================================================================


def algoritmo1_low_depth(b: int, c: int) -> tuple[Circuito, int]:
    """Variante de baixa profundidade (Corolario 10 / Proposicao 11): os comb
    sums sao computados por dobramento binario (C <- C xor (C >> 3c*2^j)) em
    vez da cadeia serial. Mesmo resultado final, mais portas, menos profundidade.
    Devolve (circuito, s) onde s e' o numero de passos de dobramento."""
    if not (b > c >= 1):
        raise ValueError("precisa de b > c >= 1")
    m = b + 2 * c
    n = m - 2

    C_val = [frozenset({m + s}) for s in range(n + 1)]   # C <- H
    C_dep = [0] * (n + 1)

    portas = 0
    j = 0
    while 3 * c * (2 ** j) <= n:
        passo = 3 * c * (2 ** j)
        novo_val = list(C_val)
        novo_dep = list(C_dep)
        for t in range(0, n + 1 - passo):
            novo_val[t] = C_val[t] ^ C_val[t + passo]
            novo_dep[t] = 1 + max(C_dep[t], C_dep[t + passo])
            portas += 1
        C_val, C_dep = novo_val, novo_dep
        j += 1

    circ = _completar_com_C(b, c, C_val, C_dep, portas)
    return circ, j


def custo_esperado(b: int, c: int) -> int:
    m = b + 2 * c
    return 3 * m - c - 3


def profundidade_esperada(b: int, c: int) -> int:
    m = b + 2 * c
    n = m - 2
    return n // (3 * c) + 4


def conferir(b: int, c: int, verbose: bool = False) -> dict:
    """Roda o Algoritmo 1 e confere contra a matriz de reducao real
    (`matriz_reducao`, ja' testada e usada em producao) e contra as formulas
    fechadas do artigo (3m-c-3 portas, profundidade <= floor(n/3c)+4)."""
    m = b + 2 * c
    f = (1 << m) | (1 << (b + c)) | (1 << b) | (1 << c) | 1

    circ = algoritmo1(b, c)
    col_real = matriz_reducao(f)
    esperado_real = [frozenset(col) for col in col_real]

    correto = circ.r == esperado_real
    custo_ok = circ.portas <= custo_esperado(b, c)   # "nunca pior", pode ser menor
    custo_bate_formula = circ.portas == custo_esperado(b, c)
    prof_ok = circ.profundidade <= profundidade_esperada(b, c)

    resultado = {
        "b": b, "c": c, "m": m,
        "correto": correto,
        "portas": circ.portas, "portas_formula": custo_esperado(b, c),
        "custo_ok": custo_ok, "custo_bate_formula": custo_bate_formula,
        "profundidade": circ.profundidade, "profundidade_formula": profundidade_esperada(b, c),
        "prof_ok": prof_ok,
    }
    if verbose:
        status = "OK" if (correto and custo_ok and prof_ok) else "FALHOU"
        print(f"b={b:>4} c={c:>4} m={m:>4}  portas={circ.portas:>5} (formula {resultado['portas_formula']:>5})"
              f"  prof={circ.profundidade:>3} (<= {resultado['profundidade_formula']:>3})"
              f"  correto={correto}  [{status}]")
    return resultado


if __name__ == "__main__":
    import random

    print("=== Exemplo 9 do artigo: degree 16, f_{6,5} ===")
    r9 = conferir(6, 5, verbose=True)
    assert r9["correto"] and r9["portas"] == 40, r9

    print("\n=== Tabela 2 do artigo (graus NIST) ===")
    casos_tabela2 = [
        (71, 46),    # m=163
        (83, 75),    # m=233
        (201, 16),   # m=233
        (179, 115),  # m=409
        (265, 72),   # m=409
        (207, 182),  # m=571
        (359, 106),  # m=571
        (527, 22),   # m=571
    ]
    for b, c in casos_tabela2:
        conferir(b, c, verbose=True)

    print("\n=== Fuzz test: 300 pares (b,c) aleatorios, m ate 800 ===")
    random.seed(0xC0FFEE)
    falhas = 0
    for _ in range(300):
        c = random.randint(1, 200)
        b = random.randint(c + 1, 800 - 2 * c)
        if b <= c:
            continue
        res = conferir(b, c)
        if not (res["correto"] and res["custo_ok"] and res["prof_ok"]):
            falhas += 1
            conferir(b, c, verbose=True)
    print(f"falhas: {falhas}/300")
