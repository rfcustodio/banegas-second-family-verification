#!/usr/bin/env python3
"""Reconstructs the Table 3 summary numbers from censo_table3_dados.json
(the raw per-degree output of censo_table3.py), without re-running the
multi-hour census."""
import json
from pathlib import Path

DADOS = Path(__file__).parent / "censo_table3_dados.json"


def melhor_custo_segunda(m, membros):
    c = max(c for b, c in membros)
    return 3 * m - c - 3


def melhor_custo_primeira(m, membros):
    if m % 5 == 0:
        c5, b5 = m // 5, 2 * m // 5
        if [b5, c5] in membros:
            return 12 * m / 5 - 1
    return 3 * m - 2


def main():
    d = json.loads(DADOS.read_text())
    segunda = {int(k): v for k, v in d["segunda"].items()}
    primeira = {int(k): v for k, v in d["primeira"].items()}
    trinomio = {int(k): v for k, v in d["trinomio"].items()}

    total_segunda = sum(len(v) for v in segunda.values())
    graus_segunda = set(segunda)
    graus_primeira = set(primeira)
    ambos = graus_segunda & graus_primeira

    segunda_mais_barata = primeira_mais_barata = empate = 0
    economias = []
    for m in sorted(ambos):
        c2 = melhor_custo_segunda(m, segunda[m])
        c1 = melhor_custo_primeira(m, primeira[m])
        if c2 < c1:
            segunda_mais_barata += 1
            economias.append((c1 - c2) / c1)
        elif c1 < c2:
            primeira_mais_barata += 1
            print(f"  first family cheaper at m={m}: first={c1} second={c2}")
        else:
            empate += 1
            print(f"  tie at m={m}: cost={c1}")

    sem_trinomio = {m for m in range(5, 1101) if not trinomio.get(m, False)}
    cobertos_segunda = sem_trinomio & graus_segunda
    cobertos_primeira = sem_trinomio & graus_primeira
    apenas_segunda = (sem_trinomio & graus_segunda) - graus_primeira
    nenhuma = sem_trinomio - graus_segunda - graus_primeira

    custos_bit = [melhor_custo_segunda(m, segunda[m]) / m for m in graus_segunda]
    media_bit = sum(custos_bit) / len(custos_bit)

    print(f"irreducible second-family members: {total_segunda}  (paper: 1508)")
    print(f"degrees with >=1 member: second={len(graus_segunda)} first={len(graus_primeira)}"
          f"  (paper: 720 / 502)")
    print(f"degrees with both families: {len(ambos)}  (paper: 405)")
    print(f"  second family cheaper: {segunda_mais_barata}  (paper: 403, mean saving "
          f"{sum(economias)/len(economias)*100:.1f}% -- paper: 7.3%)")
    print(f"  first family cheaper: {primeira_mais_barata}  (paper: 1, m=155)")
    print(f"  tie: {empate}  (paper: 1, m=5)")
    print(f"degrees without an irreducible trinomial: {len(sem_trinomio)}  (paper: 502)")
    print(f"  covered by second/first family: {len(cobertos_segunda)} / {len(cobertos_primeira)}"
          f"  (paper: 288 / 229)")
    print(f"  covered by second family only: {len(apenas_segunda)}  (paper: 112)")
    print(f"  covered by neither: {len(nenhuma)}  (paper: 161)")
    print(f"mean cost per bit (best generic second-family member): {media_bit:.2f}  (paper: 2.77)")


if __name__ == "__main__":
    main()
