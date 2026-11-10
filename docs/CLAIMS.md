# Claims of the paper and how each one is verified

Numbering follows `paper/main.pdf` (IEEE Access version). "Proof" means the argument is
in the paper; the scripts check the statement independently of the proof.

There are three levels of checks:

* **quick**: `./run_quick_checks.sh` (standard library only, about 1 minute), on small
  degrees (default `m <= 120`; `make check-full` uses `m <= 300`);
* **full**: `make verify-all`, which runs `verification/run_all.sh` (gcc, Python 3,
  `python-sat`, about 15 minutes) over **all** 201,117 members with `m <= 1100`, the range
  reported in the paper, and compares the output with `verification/expected_output.txt`;
* **independent**: `independent/`, a second implementation written from the text alone.

Symbolic checks compare each output of a program with the corresponding row of the
reduction matrix, so they prove correctness for all inputs of that `(b, c)`.

## Section III: the second family

| Item | Statement (short) | Kind | Verified by | Result |
|---|---|---|---|---|
| Def. 1 | `f_{b,c} = x^(b+2c)+x^(b+c)+x^b+x^c+1`, `m = b+2c`, `n = m-2` | definition | - | - |
| Prop. 2 (i)-(v) | `x^m ≡ (x^b+1)(x^c+1)`; `(x^c+1) f = x^(b+3c)+x^b+x^(2c)+1`; `c <= floor((m-1)/3)`, `b ≡ m mod 2`; `f = G(x^γ)`; `b = 2c` equally spaced | proof + check | quick: `checks/verify_statements.py` | all members `m <= 300`: PASS |
| Def. 3 | special members: base polynomial `G` of degree `κ <= 7` (`b/c` in `{3/2, 2, 3, 4, 5}`) | definition | - | - |
| Prop. 4 (i) | reduction splits into `γ` strips modulo `G`; `Red(f) <= (γ-1) R1(G) + R2(G)` | proof + check | full: `verification/alg1verify.c` (strip check), `verification/compose_strips.py`, `verification/compose_sat.py` | PASS |
| Prop. 4 (ii) | Algorithm 1 never mixes strips; `3κ-c'-3` gates on the last strip, `3κ-c'` on the others | proof + check | full: `verification/alg1verify.c` | all 201,117 members: PASS |
| Eq. (2) | strip bound `3m-c-3-(γ-1)δ1(G)-δ2(G)` | algebra | - | - |
| Table 2 | optimal `R2`, `R1` for the five base polynomials and the bounds `7m/4-1`, `12m/5-2`, `5m/2-1`, `18m/7-2` | SAT proof + composition | full: `verification/exact_small.py` (`R2`), `verification/exact_base.py` (`R1`: a program with `R1` gates, none with `R1-1`), `verification/compose_sat.py` (composed over 183 and 157 members up to `m = 1100`) | all optimal; 0 failures |
| Text | greedy sweep over the 163 reduced pairs with `4 <= κ <= 40`: only the five base polynomials beat the closed form | computation | full: `verification/greedy.c strip 200 40`; `generator/strips.py` | reproduced |
| Text | `Red(f_{6,1}) = 19`, `Red(f_{5,2}) = 21` | SAT proof | full: `verification/exact_small.py` | reproduced |

## Section IV: closed form for the quotient

| Item | Statement (short) | Kind | Verified by | Result |
|---|---|---|---|---|
| Lemma 5 | division identities (3) and (4) | proof + check | quick: `checks/verify_statements.py` (random products against long division) | PASS |
| Def. 6 | comb sums `C_t` | definition | - | - |
| Thm. 7 | closed forms (6) for `q_j`, (7) for `U_k`, (8) for `r_i` | proof + symbolic check | quick: `checks/verify_statements.py` | all members `m <= 300`: PASS |
| Fig. 1 | `C_1` and `U_2` for `b = 11`, `c = 2` | example | by hand: `U_2 = C_0 + C_4 + h_13` | correct |

## Section V: the closed-form program (Algorithm 1)

| Item | Statement (short) | Kind | Verified by | Result |
|---|---|---|---|---|
| Thm. 8 | Algorithm 1 is correct and uses at most `3m-c-3` XORs | proof + symbolic check | quick: `checks/verify_statements.py`; full: `verification/alg1verify.c`; independent: `independent/second_family.py` | all 201,117 members `m <= 1100`: exactly `3m-c-3` |
| Thm. 8 (proof) | coincident operands occur only for `b = 2c` | computation | full: `verification/alg1verify.c` | 274 special members, 0 generic |
| Prop. 9 | depth at most `floor(n/(3c))+4`, at most 5 when `b <= 4c+1` | proof + check | quick and full | PASS |
| Prop. 9 (text) | measured depth `floor(n/(3c))+3` in 97% of the 14,748 pairs `7 <= m < 300` | measurement | full: `verification/alg1verify.c`; quick: `checks/verify_statements.py --mmax 300` | 14,358 / 14,748 (14,285 in `generator/fam2.py`, which reuses the coincident values of the 73 equally spaced members) |
| Cor. 10 | multiplier with `m^2+m-c-2` XORs | identity + check | quick: `checks/verify_statements.py` | PASS |
| Ex. 11, Table 3 | `f_{6,5}`: irreducible, 40 XORs, `dXOR = 54`, `CX = 44` | computation | quick; full (`greedy one`) | PASS |

## Section VI: the chain construction (Algorithm 2)

| Item | Statement (short) | Kind | Verified by | Result |
|---|---|---|---|---|
| Lemma 12 | `E_t = h_t + P_(t+2c)`, `P_k = h_(k-c) + E_(k+c)`, `P_k = E_(k-c) + E_k`; boundary values | proof + check | quick: `checks/verify_chain.py` | PASS |
| Thm. 13 | Algorithm 2 is correct with exactly `3m-3-N(b,c)` XORs; closed formula for `N`; larger / equal / smaller than `3m-c-3` for `b < 2c` / `2c <= b <= 4c` / `b >= 4c+1`; `<= 8m/3+c-3` | proof + symbolic check | quick: `checks/verify_chain.py` (`m <= 120`); full: `algorithm2/alg2verify.c` | all 201,117 members `m <= 1100`: PASS; improved in 100,284 |
| Text | multiplier `m^2+m-2-N(b,c)` | algebra | - | - |
| Text | `f_{6,1}`: 19, `f_{5,1}`: 16, `f_{7,1}`, `f_{8,1}`, `f_{9,1}`: 22, 24, 27 | computation | quick: `checks/verify_chain.py` | PASS |
| Ex. 14 | `f_{8,1}`: 12 gates before the outputs, 24 in total | computation | quick: `checks/verify_chain.py`; `python3 algorithm2/alg2prog.py 8 1 p` | PASS |
| Prop. 15 | depth at most `2 floor((n-c)/(3c))+6`; measured at most `+5` | proof + check | quick and full | max excess `-1` |
| Text | `m = 571`, `c = 22`: 1534 gates, depth 20 (Algorithm 1: 1688, depth 11) | computation | quick: `checks/verify_chain.py`; full | PASS |
| Text | MaxSAT: each chain is optimal within the identity family, except chains with three indices (`b < 2c`) | MaxSAT | `algorithm2/chaincheck.py` (all chain lengths `<= 1100`; several minutes, not in `run_all.sh`) | 0 mismatches |

## Section VII: word level and low depth

| Item | Statement (short) | Kind | Verified by | Result |
|---|---|---|---|---|
| Cor. 16 | word-level formula for `C, Q, U, R` | proof + random check | quick: `checks/verify_statements.py`; `generator/wordlevel.py`; full: `verification/alg1verify.c` | PASS |
| Text | `ν+5` shift-and-XOR operations, at most six when `b <= 4c+1` | counting | - | - |
| Prop. 17 | low-depth variant: gate bound and depth `<= ν+4` | proof + symbolic check | quick: `generator/lowdepth.py --all 160`; full: `verification/alg1verify.c` (all `m <= 1100`) | 0 violations |
| Text | `m = 571, c = 22`: doubling 2474 gates, depth 7 (+786, about 47%) | computation | full: `verification/alg1verify.c 571 571` | reproduced |

## Section VIII: comparison with the greedy count

| Item | Statement (short) | Verified by | Result |
|---|---|---|---|
| Obs. 18 | 3,674 pairs, 3,541 generic (`5 <= m <= 150`) | quick: `checks/analyze_paar150.py`; full: `verification/greedy.c` + `analyze_greedy.py`; independent: `independent/observacao12.py` | reproduced |
| Obs. 18 (a)-(d) | never longer than greedy; 879 with `b < 2c` (`CX = 2m+3c-3`); 1,312 with `2c < b < 6c` (equal); 392 of 1,350 worse for `b >= 6c`, up to 112 | same | reproduced |
| Obs. 18 (text) | random tie-breaking improved 212 generic members by at most 12 (an independent rerun gives 213 and 13), all with `b >= 6c`, closing the gap once | same | reproduced (the two figures come from different random seeds) |
| Obs. 18 (text) | special members: greedy values of `R1`, `R2`; `12m/5-2` when `b = 3c` | same | reproduced |
| Fig. 2 | `CX - (3m-c-3)` versus `b/c` | `generator/make_figures.py` from `data/paar150.txt` | regenerated |
| Table 4 | 8 members at the NIST degrees: `dXOR`, `CX`, `3m-c-3`, depth, `3m-3-N` | quick: `checks/reproduce_tables.py`, `checks/verify_chain.py`; full | all entries reproduced |
| Text | Boyar and Peralta: `f_{5,2}`, `f_{4,3}`, `f_{3,2}` give 22, 24, 16 | full: `verification/boyar_peralta.py` | reproduced |
| Table 5 | exact minima (SAT), best bound, heuristic column (greedy with 500 random runs, Boyar and Peralta) | full: `verification/exact_small.py`, `verification/heuristic_small.py` | all entries reproduced |

## Section IX: comparison with the first family and other polynomials

| Item | Statement (short) | Verified by | Result |
|---|---|---|---|
| Table 1 | literature values | citations in the paper | not computational |
| Table 6 | census for `5 <= m <= 1100` with both constructions | quick: `checks/compare_censuses.py` (and the member-by-member comparison with the independent census); full: `verification/census.c`, `analyze_census.py`, `algorithm2/census_alg2.py` | all entries reproduced; both censuses identical |
| Text | mean cost per bit 2.70 (2.77 with Theorem 8 alone); 379 degrees improved, 160 without trinomials, up to 11.1% (`m = 975`: 2921 to 2598); mean saving 9.7% (7.3%) | quick: `checks/compare_censuses.py` | reproduced |
| Text | `m = 5` and `m = 155` depend on special members (10 vs 11; 370 vs 371, best generic 411) | quick: `checks/compare_censuses.py` | reproduced |
| Text | 25 degrees `≡ 0 mod 8` with members; 40, 126 and 384 XORs | quick: `checks/reproduce_tables.py` | reproduced |
| Fig. 3 | cost per bit by degree (no-trinomial degrees), both constructions | `generator/make_figures.py` from `data/census_alg2.json` | regenerated |
| Prop. 19 | irreducible special members: `f_{2,1}(x^(5^i))`, `f_{3,1}(x^(31^i))`, `f_{4,1}(x^(3^i 7^j))` | proof + check | quick: `checks/reproduce_tables.py` (the special members found by the census are exactly those predicted) | PASS |
| Table 7 | the 15 irreducible special members with `5 <= m <= 1100`: closed form, strip bound, best generic member | quick: `checks/reproduce_tables.py`; `generator/strips.py --special 1100` | all entries reproduced |
| Table 8 | costs at the NIST degrees; savings 22.9%, 23.7%, 9.7%, 10.7% | quick: `checks/reproduce_tables.py` | reproduced |

## Abstract

Every number in the abstract appears in one of the rows above (Theorems 8 and 13,
Proposition 9, Table 2, Table 6, Table 8, and the size of the verification).

## Not verified by code

* The proofs themselves (they are checked by reading; the scripts test the statements).
* Literature values in Table 1 and the description of related work.
* Interpretations in the text, such as why the five base polynomials admit short strip
  programs or what the greedy heuristic misses.
