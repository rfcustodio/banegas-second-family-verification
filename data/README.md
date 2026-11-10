# `data/`: raw outputs of the experiments

All files are plain text (or JSON) and can be regenerated with the programs in
`generator/`. `xorred` below is `generator/xorred.c` compiled with
`gcc -O2 -o xorred generator/xorred.c`.

| File | Format (one record per line) | Produced by | Used for |
|---|---|---|---|
| `paar150.txt` | `m a b c dXOR CX depth_CX RG depth_RG`, with `a = b + c`. `dXOR` is the direct count (sum of row weights minus one), `CX` the Conta-XOR count with lexicographic tie-breaking, `RG` the best of `CX` and 20 greedy runs with random tie-breaking (seed 5 or 6), and the depths are XOR depths. One line per member `b > c >= 1`, `5 <= m <= 150` (3,674 lines). | `python3 -c "..."` listing the pairs (see below), then `xorred list 20 5 < pairs` | Observation 18, Figure 2 (`checks/analyze_paar150.py`) |
| `fam2_irr.txt` | `m b c` for every irreducible `x^(b+2c)+x^(b+c)+x^b+x^c+1`, `5 <= m <= 1100` (1,508 lines). | `xorred fam2 5 1100` | Table 6, Table 9, Figure 3, Section IX |
| `fam1_irr.txt` | `m b c` for every irreducible `x^(2b+c)+x^(b+c)+x^b+x^c+1` (first family, BCP), `5 <= m <= 1100` (755 lines). | `xorred fam1 5 1100` | Table 6, Table 9, Figure 3 |
| `tri.txt` | `m k`: smallest `k <= m/2` with `x^m+x^k+1` irreducible, for the degrees `2 <= m <= 1100` that have one. Degrees absent from the file have no irreducible trinomial. | `xorred tri 2 1100` | Table 6, Figure 3 |
| `greedy_beyond150.txt` | `m b c dXOR CX bestRandom 3m-c-3` (one header line; `bestRandom = -1`: no random runs) for every member with `151 <= m <= 300` and with `m = 500, 800, 1100` (11,973 lines), greedy with lexicographic ties. | `verification/greedy_beyond150.sh` (`make greedy-beyond150`) | Section VIII, paragraph after Figure 2 |
| `type1_irr.txt`, `type2_irr.txt` | `m n` for every irreducible type I `x^m+x^(n+1)+x^n+x+1` (`2 <= n <= m/2-1`) and type II `x^m+x^(n+2)+x^(n+1)+x^n+1` (`1 <= n <= m/2-1`), `5 <= m <= 1100`. | `verification/census t1 5 1100`, `census t2 5 1100` | Table 7 |
| `rmh_class2_irr.txt` | `m s` for every irreducible `x^m+x^(m-s)+x^(m-2s)+x^(m-3s)+1`, `(m-1)/8 <= s <= (m-1)/3`. | `verification/census esp 5 1100` | Section IX-C |
| `pent_min.txt` | `m k3 k2 k1`: the first irreducible `x^m+x^k3+x^k2+x^k1+1` with `k3 <= m/2` (smallest `k3`, then `k2`, then `k1`). | `verification/census pmin 5 1100` | Table 7 |
| `other_families.json` | Costs per degree without trinomials used in Table 7, for each family (type II: greedy count minimized over the irreducible members). | `verification/other_families.py` | Table 7, `checks/compare_other_families.py` |
| `multiplier.json` | Karatsuba product counts at `m = 163, 571` and the rows of Table 10, one per irreducible member of the two families and one per NIST pentanomial (reduction, schoolbook and Karatsuba multiplier, squaring with lexicographic ties, squaring with the best of 20 randomized runs). | `verification/multiplier.py` | Table 10, `checks/compare_multiplier.py` |
| `census_alg2.json` | Like `census.json`, with the best member per degree under both constructions (`F2`, Theorems 8 and 13 and the strip bound for special members), under Theorem 8 alone (`F2_alg1`), and the best generic member (`F2gen`). | `algorithm2/census_alg2.py` | Table 6, Figure 3, Section IX |
| `census.json` | `{"F2": {m: [cost, b, c]}, "F1": {m: [cost, b, c]}, "T": [m, ...]}`: best member per degree of each family (cost by Theorem 8, by BCP's `3m-2` or `12m/5-1`, and `7m/4-1` for equally spaced members), and the list of degrees with trinomials. | derived from the three files above | earlier version of Figure 3; `verification/analyze_census.py` |

The list of pairs for `paar150.txt` was generated with

```bash
python3 -c "
for m in range(5,151):
    for c in range(1,m):
        b=m-2*c
        if b>c: print(m,b+c,b,c)" > pairs150.txt
./xorred list 20 5 < pairs150.txt > paar150.txt
```

(in the original run the list was split in two halves processed in parallel with seeds 5
and 6; the deterministic columns `dXOR`, `CX` and the depths do not depend on the seed).

Irreducibility is decided with Rabin's test. The censuses in `fam1_irr.txt`,
`fam2_irr.txt` and `tri.txt` agree member by member with the independent census in
`independent/censo_table3_dados.json` (`checks/compare_censuses.py`).
