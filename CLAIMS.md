# Claims of the paper and how each one is verified

Numbering follows `paper/artigo2.pdf`. "Proof" means the argument is in the paper;
the scripts check the statement independently of the proof. "Both suites" means the
number is reproduced by the authors' code (`generator/`, `checks/`) and by the separate
re-implementation in `independent/`.

Ranges: symbolic checks run over **all** members `b > c >= 1` with `m <= 300` when
called with `--mmax 300` (default `m <= 120`); random tests use field products of
random elements.

## Definitions and structural results

| Item | Statement (short) | Kind | Verified by | Range / result |
|---|---|---|---|---|
| Def. 1 | `f_{b,c} = x^(b+2c)+x^(b+c)+x^b+x^c+1`, `m = b+2c` | definition | - | - |
| Prop. 2 (i) | `x^m ≡ (x^b+1)(x^c+1) mod f` | proof + check | `checks/verify_statements.py` | all 14,850 members `m <= 300`: PASS |
| Prop. 2 (ii) | `(x^c+1) f = x^(b+3c)+x^b+x^(2c)+1`; `x^b(x^(3c)+1) ≡ (x^c+1)^2` | proof + check | `checks/verify_statements.py` | PASS |
| Prop. 2 (iii) | `c <= floor((m-1)/3)`, `b ≡ m mod 2` | proof + check | `checks/verify_statements.py` | PASS |
| Prop. 2 (iv) | `gcd(b,c) = g > 1` implies `f(x) = G(x^g)` | proof + check | `checks/verify_statements.py` | PASS |
| Prop. 2 (v) | `b = 2c` gives the equally spaced pentanomial | proof + check | `checks/verify_statements.py` | PASS |
| Lemma 3 | division identities (2) and (3) | proof (standard) + check | `checks/verify_statements.py` (random products vs long division) | 32,835 products: PASS |
| Def. 4 | comb sums `C_t` | definition | - | - |
| Thm. 5 | closed forms (5) for `q_j`, (6) for `U_k`, (7) for `r_i` | proof + symbolic check | `checks/verify_statements.py` compares (5)-(6) with the recurrence (4), and (7) with the rows of the reduction matrix | all members `m <= 300`: PASS |

## Main result and its consequences

| Item | Statement (short) | Kind | Verified by | Range / result |
|---|---|---|---|---|
| Thm. 6 | Algorithm 1 is correct and uses at most `3m-c-3` XORs | proof + symbolic check | `generator/fam2.py` (via `checks/verify_statements.py`); `independent/second_family.py` | all 14,850 members `m <= 300`: PASS (both suites); exactly `3m-c-3` on generic members |
| Prop. 7 | depth at most `floor(n/3c)+4` | proof + check | `checks/verify_statements.py`; `independent/second_family.py` | PASS |
| Prop. 7 (text) | measured depth equals `floor(n/3c)+3` in 97% of the 14,748 pairs `7 <= m < 300` | measurement | `checks/verify_statements.py --mmax 300` (printed below the Prop. 7 line) | 14,285 / 14,748 |
| Cor. 8 | multiplier with `m^2+m-c-2` XORs | identity + check | `checks/verify_statements.py` (schoolbook product followed by Cor. 10, random field products) | PASS |
| Ex. 9 | `f_{6,5}`: irreducible, 40 XORs, `dXOR = 54`, `CX = 44` | computation | `checks/verify_statements.py`; `independent/second_family.py` | PASS |
| Cor. 10 | word-level formula `C, Q, U, R` | proof + random check | `checks/verify_statements.py`; `generator/wordlevel.py` | PASS |
| Prop. 11 | low-depth variant: gate bound and depth `<= s+4` | proof + symbolic check | `generator/lowdepth.py --all 260`; `independent/second_family.py` | 11,048 members `m < 260`: 0 violations |
| Prop. 11 (text) | `m = 571, c = 22`: chain 1688 gates / depth 11, doubling 2474 / depth 7 | computation | `generator/lowdepth.py 527 22`, `generator/fam2.py 527 22` | reproduced (both suites) |

## Comparison with the greedy count (Section 7)

| Item | Statement (short) | Verified by | Result |
|---|---|---|---|
| Obs. 12 | 3,674 pairs, 3,541 generic (`5 <= m <= 150`) | `checks/analyze_paar150.py` (from `data/paar150.txt`); `independent/observacao12.py` (recomputes the greedy counts) | reproduced (both suites) |
| Obs. 12 (a) | closed form never longer than the greedy values on generic members | same | reproduced |
| Obs. 12 (b) | 879 members with `b < 2c`: `CX = 2m+3c-3`, gain `2c-b` | same | reproduced (both suites) |
| Obs. 12 (c) | 1,312 members with `2c < b < 6c`: `CX = 3m-c-3` | same | reproduced (both suites) |
| Obs. 12 (d) | `b >= 6c`: greedy worse in 392 of 1,350, by up to 112 | same | reproduced (both suites) |
| Obs. 12 (text) | effect of random tie-breaking | `checks/analyze_paar150.py` | **corrected**: the first draft said "changed the outcome in only one case"; the data show 212 generic members improved (all with `b >= 6c`, by at most 12 XORs), and only one of them reaches `3m-c-3`. The sentence in `paper/artigo2.tex` was fixed accordingly. |
| Obs. 12 (text) | special members: greedy can be shorter, e.g. `12m/5-2` when `b = 3c` | `checks/analyze_paar150.py` | reproduced (30 of 30 members with `b = 3c`) |
| Fig. 2 | `CX - (3m-c-3)` versus `b/c` | `generator/make_figures.py` from `data/paar150.txt` | regenerated |
| Small degrees | `f_{5,2}`, `f_{4,3}`: Boyar-Peralta finds 22 and 24 (= closed form), greedy 22 and 26; `f_{3,2}`: 16 vs greedy 17 | `python3 generator/smallm.py 9 7 5 2 10`, `... 10 7 4 3 10`, `... 7 5 3 2 10` (needs `numpy`; a few minutes) | reproduced in the original run |
| Table 2 | 8 members at the NIST degrees: irreducibility, `dXOR`, `CX`, `3m-c-3`, depth | `checks/reproduce_tables.py`; `independent/second_family.py` (gate count and depth) | all entries reproduced |

## Comparison with other polynomials (Section 8)

| Item | Statement (short) | Verified by | Result |
|---|---|---|---|
| Table 1 | literature values | citations in the paper | not computational |
| Table 3 | census for `5 <= m <= 1100` | `checks/compare_censuses.py` (authors' census, and comparison with the independent census member by member); `independent/table3_summary.py` | all entries reproduced; both censuses identical |
| Table 4 | best known costs at the NIST degrees | `checks/reproduce_tables.py` | reproduced; NIST pentanomial values are the Conta-XOR counts of Banegas' thesis, recomputed |
| Fig. 3 | cost per bit by degree (no-trinomial degrees) | `generator/make_figures.py` from `data/census.json` | regenerated |
| Text | 25 degrees `≡ 0 mod 8` with members; `x^48+...` 126 XORs; `x^144+...` 384 XORs; `m = 155` exception (371 vs 411); savings 22.9% / 23.7% / 9.7% / 10.7% | `checks/reproduce_tables.py` | reproduced |

## Abstract

Every number in the abstract appears in one of the rows above (Thm. 6, Prop. 7,
Cor. 8, Obs. 12, Table 3, Table 4).

## Not verified by code

* The proofs themselves (they are checked by reading; the scripts test the statements).
* Literature values in Table 1 and the description of related work.
* Statements about what the greedy heuristic "misses" in the Discussion, which are
  interpretations of the measurements above.
