# Verification of the computational claims

Independent re-implementations used to check every number in the paper up to
degree 1100. Run `sh run_all.sh` (gcc, Python 3 and `python-sat`, about 15 minutes on 2 cores) and
compare with `expected_output.txt`; only the running times printed by the SAT scripts may differ.

| File | What it checks |
|---|---|
| `alg1verify.c` | Algorithm 1 for every `b > c >= 1` with `m <= 1100` (201,117 members): exact symbolic equality with the reduction matrix, gate count `3m-c-3`, depth bound and statistics, low-depth variant (comb sums, gate formula, depth `<= s+4`), strip decomposition of Proposition 4(ii), word-level corollary on random inputs, and coincident gate values. |
| `census.c` | Irreducibility (small-factor sieve plus Rabin's test) of all second-family members, first-family members, trinomials, type I and type II pentanomials, the class `x^m+x^(m-s)+x^(m-2s)+x^(m-3s)+1` and the first pentanomial with `k3 <= m/2`, for `m <= 1100`. |
| `analyze_census.py` | All census figures for Algorithm 1 alone: Table 6, Section IX text, NIST table, special members (Table 8), comparison with `data/census.json`. |
| `greedy.c` | Paar/Conta-XOR greedy (lexicographic and randomized ties; mode `sq` for the reduction of a square): Observation 18, Example 11 (Table 3), the counts of Tables 4 and 9, and the strip programs of the 163 reduced pairs with `4 <= kappa <= 40` (Section III). |
| `analyze_greedy.py` | Observation 18 statistics against `data/paar150.txt`. |
| `greedy_beyond150.sh`, `analyze_greedy_beyond150.py` | The regularities of Observation 18 beyond `m = 150` (Section VIII, paragraph after Figure 2): greedy count for all members with `151 <= m <= 300` and for `m = 500, 800, 1100` (about 4 minutes, not part of `run_all.sh`), compared with `data/greedy_beyond150.txt`. |
| `compose_strips.py` | Composes the greedy strip programs over all strips of the 992 special members with `m <= 1100` and checks them symbolically. |
| `other_families.py` | Section IX-C and Table 7: comparison with type I, type II and general pentanomials over the 502 degrees without trinomials (type II costs by the greedy count). |
| `karatsuba.py`, `multiplier.py` | Table 10 (Section IX-E): recursive Karatsuba product (schoolbook, Karatsuba and Bernstein's refined split, cheapest at each size; built explicitly and tested on random inputs), full multiplier totals and squaring costs (`greedy sq`, reduction of a square, lexicographic ties and best of 20 randomized runs) for every irreducible member of both families at degrees 163 and 571 (read from `data/fam2_irr.txt` and `data/fam1_irr.txt`) and for the NIST pentanomials. The squaring count is minimized separately in each family, because the modulus with the smallest reduction bound need not have the cheapest squaring (changed in v23). |
| `boyar_peralta.py` | Boyar and Peralta heuristic for `f_{5,2}`, `f_{4,3}` and `f_{3,2}` (Section VIII). |
| `depth_table3.py` | Depth column of Table 4 (the file name follows an earlier numbering). |
| `slp_sat.py` | SAT encoding (pysat, CaDiCaL) of the shortest straight-line program problem for a set of XOR targets. |
| `exact_base.py` | Proves that the `R_1(G)` values of Table 2 are optimal (a program with `R_1` gates exists, none with `R_1 - 1`). |
| `compose_sat.py` | Composes the optimal SAT programs of `f_{4,1}` and `f_{5,1}` over every strip member with `m <= 1100` and checks the bounds `15*gamma-1` and `18*gamma-2`. |
| `exact_small.py` | Exact minima of Table 5 (about 40 s; for the `<=` entries only the existence of the program is tested). |
| `heuristic_small.py` | Heuristic column of Table 5: greedy with 500 randomized runs and 10 runs of Boyar and Peralta. |

The SAT scripts need `pip install python-sat`. See also `../algorithm2` for the chain construction (Algorithm 2, Theorem 13), which
`run_all.sh` also verifies.
