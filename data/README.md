# `data/`: raw outputs of the experiments

All files are plain text (or JSON) and can be regenerated with the programs in
`generator/`. `xorred` below is `generator/xorred.c` compiled with
`gcc -O2 -o xorred generator/xorred.c`.

| File | Format (one record per line) | Produced by | Used for |
|---|---|---|---|
| `paar150.txt` | `m a b c dXOR CX depth_CX RG depth_RG`, with `a = b + c`. `dXOR` is the direct count (sum of row weights minus one), `CX` the Conta-XOR count with lexicographic tie-breaking, `RG` the best of `CX` and 20 greedy runs with random tie-breaking (seed 5 or 6), and the depths are XOR depths. One line per member `b > c >= 1`, `5 <= m <= 150` (3,674 lines). | `python3 -c "..."` listing the pairs (see below), then `xorred list 20 5 < pairs` | Observation 12, Figure 2 (`checks/analyze_paar150.py`) |
| `fam2_irr.txt` | `m b c` for every irreducible `x^(b+2c)+x^(b+c)+x^b+x^c+1`, `5 <= m <= 1100` (1,508 lines). | `xorred fam2 5 1100` | Table 3, Table 4, Figure 3, Section 8 |
| `fam1_irr.txt` | `m b c` for every irreducible `x^(2b+c)+x^(b+c)+x^b+x^c+1` (first family, BCP), `5 <= m <= 1100` (755 lines). | `xorred fam1 5 1100` | Table 3, Table 4, Figure 3 |
| `tri.txt` | `m k`: smallest `k <= m/2` with `x^m+x^k+1` irreducible, for the degrees `2 <= m <= 1100` that have one. Degrees absent from the file have no irreducible trinomial. | `xorred tri 2 1100` | Table 3, Figure 3 |
| `census.json` | `{"F2": {m: [cost, b, c]}, "F1": {m: [cost, b, c]}, "T": [m, ...]}`: best member per degree of each family (cost by Theorem 6, by BCP's `3m-2` or `12m/5-1`, and `7m/4-1` for equally spaced members), and the list of degrees with trinomials. | derived from the three files above | Figure 3 |

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
