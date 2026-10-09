#!/usr/bin/env python3
"""Reproducao independente da Observacao 12 do artigo (Secao 7): comparacao
entre o ContaXOR guloso (`conta_xor`, ja' validado noutra parte do projeto) e
a formula fechada 3m-c-3 do Algoritmo 1, para todos os pares com 5<=m<=150.

Nao usa nada de second_family.py de proposito -- e' um caminho de codigo
totalmente separado (algoritmo guloso, nao a formula fechada), pra servir de
conferencia cruzada de verdade."""
from fractions import Fraction

from contaxor import matriz_reducao, conta_xor


def especial(b: int, c: int) -> bool:
    return Fraction(b, c) in {Fraction(3, 2), Fraction(2), Fraction(3), Fraction(4), Fraction(5)}


def main():
    total = generico = 0
    b_lt_2c = match_a = 0
    entre = match_b = 0
    ge6c = greedy_pior = 0
    max_diff = 0
    quebrou = []

    for m in range(5, 151):
        c_max = (m - 1) // 3
        for c in range(1, c_max + 1):
            b = m - 2 * c
            if b <= c:
                continue
            total += 1
            f = (1 << m) | (1 << (b + c)) | (1 << b) | (1 << c) | 1
            col = matriz_reducao(f)
            cx = conta_xor(col, 2 * m - 1).xors
            formula = 3 * m - c - 3

            if cx < formula:
                quebrou.append((b, c, m, cx, formula, especial(b, c)))
                continue

            if especial(b, c):
                continue
            generico += 1

            if b < 2 * c:
                b_lt_2c += 1
                if cx == 2 * m + 3 * c - 3:
                    match_a += 1
            elif b < 6 * c:
                entre += 1
                if cx == formula:
                    match_b += 1
            else:
                ge6c += 1
                if cx > formula:
                    greedy_pior += 1
                    max_diff = max(max_diff, cx - formula)

    nao_especiais_quebrados = [q for q in quebrou if not q[5]]

    print(f"total de pares (5<=m<=150): {total}  (artigo: 3674)")
    print(f"genericos: {generico}  (artigo: 3541)")
    print(f"greedy < formula (so' deveria acontecer em membros especiais): {len(quebrou)}")
    print(f"  dos quais NAO especiais (isso sim seria bug): {len(nao_especiais_quebrados)}")
    for q in nao_especiais_quebrados:
        print("   ", q)
    print()
    print(f"b<2c: {b_lt_2c} membros (artigo: 879), CX==2m+3c-3 em {match_a}")
    print(f"2c<b<6c: {entre} membros (artigo: 1312), CX==3m-c-3 em {match_b}")
    print(f"b>=6c: {ge6c} membros (artigo: 1350), greedy pior em {greedy_pior} (artigo: 392), "
          f"diff maxima {max_diff} (artigo: 112)")


if __name__ == "__main__":
    main()
