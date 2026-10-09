#!/usr/bin/env python3
"""Censo independente da Tabela 3 do artigo (irredutibilidade, 5<=m<=1100),
rodado em blocos pra nao perder progresso se a sessao cair no meio (ja
aconteceu uma vez). Cada chamada roda um intervalo [m_ini, m_fim] e funde o
resultado no JSON persistente -- chamadas repetidas pulam graus ja' prontos,
entao e' seguro rodar de novo se travar no meio de um bloco.

Uso: python3 censo_table3.py <m_ini> <m_fim>
"""
import sys
import time
import json
from pathlib import Path

from contaxor import eh_irredutivel

DADOS = Path(__file__).parent / "censo_table3_dados.json"


def build(m, a, b, c):
    return (1 << m) | (1 << a) | (1 << b) | (1 << c) | 1


def carregar():
    if DADOS.exists():
        with DADOS.open() as fh:
            d = json.load(fh)
    else:
        d = {"segunda": {}, "primeira": {}, "trinomio": {}}
    return d


def salvar(d):
    tmp = DADOS.with_suffix(".tmp")
    with tmp.open("w") as fh:
        json.dump(d, fh)
    tmp.replace(DADOS)   # escrita atomica, nao corrompe se cair no meio


def grau_pronto(d, m):
    return str(m) in d["segunda"] or str(m) in d["trinomio"]
    # trinomio sempre grava (True/False) pra todo m computado, entao sua
    # presenca sozinha ja' basta pra saber que o grau m foi processado


def processa_grau(m):
    # segunda familia: m = b+2c, b>c>=1
    membros2 = []
    c_max = (m - 1) // 3
    for c in range(1, c_max + 1):
        b = m - 2 * c
        if b <= c:
            continue
        if eh_irredutivel(build(m, b + c, b, c)):
            membros2.append([b, c])

    # primeira familia: m = 2b+c, b>c>=1
    membros1 = []
    b_min = m // 3 + 1
    b_max = (m - 1) // 2
    for b in range(b_min, b_max + 1):
        c = m - 2 * b
        if not (1 <= c < b):
            continue
        if eh_irredutivel(build(m, b + c, b, c)):
            membros1.append([b, c])

    # trinomio: existe x^m+x^k+1 irredutivel com k<=m/2?
    tem_trinomio = False
    for k in range(1, m // 2 + 1):
        if eh_irredutivel((1 << m) | (1 << k) | 1):
            tem_trinomio = True
            break

    return membros2, membros1, tem_trinomio


def main():
    m_ini, m_fim = int(sys.argv[1]), int(sys.argv[2])
    d = carregar()

    t0 = time.time()
    feitos_agora = 0
    for m in range(m_ini, m_fim + 1):
        if grau_pronto(d, m):
            continue
        membros2, membros1, tem_tri = processa_grau(m)
        if membros2:
            d["segunda"][str(m)] = membros2
        if membros1:
            d["primeira"][str(m)] = membros1
        d["trinomio"][str(m)] = tem_tri
        feitos_agora += 1

    salvar(d)
    dt = time.time() - t0
    ja_prontos = (m_fim - m_ini + 1) - feitos_agora
    print(f"bloco [{m_ini},{m_fim}]: {feitos_agora} graus novos processados "
          f"({ja_prontos} ja' estavam prontos de antes) em {dt:.1f}s", flush=True)
    print(f"total acumulado no arquivo: {len(d['trinomio'])} graus", flush=True)


if __name__ == "__main__":
    main()
