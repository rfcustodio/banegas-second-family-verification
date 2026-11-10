# Banegas' second family of irreducible pentanomials

**Code, data and verification for the paper**

> M. Tomaszewski, R. F. Custódio, G. Banegas and D. Panario,
> *Efficient Closed-Form Reduction for Banegas' Second Family of Pentanomials*
> (submitted to IEEE Access).

This repository holds the paper, all the code and data behind it, and scripts that
check every statement of the paper. It serves the reviewers and readers who want to
reproduce the results, and the co-authors who want to check and improve the text.

**Start here:** [1. What the paper is about](#1-what-the-paper-is-about) ·
[2. Check everything](#2-check-everything) ·
[3. I want to check a specific statement](#3-i-want-to-check-a-specific-statement) ·
[4. Tour of the folders](#4-tour-of-the-folders) ·
[5. How we work together](#5-how-we-work-together) ·
[Resumo em português](#resumo-em-português)

---

## 1. What the paper is about

**The setting.** In the binary field `GF(2^m)` an element is a polynomial of degree
less than `m` with bits as coefficients. Multiplying two elements has two stages:

1. a carry-less product, which gives a polynomial `D` of degree up to `2m − 2`;
2. a **reduction** of `D` modulo a fixed irreducible polynomial `f` of degree `m`.

Stage 1 does not depend on `f`. Stage 2 depends only on `f`, and in hardware (or in
bitsliced software) its cost is the number of 2-input **XOR gates**. Choosing a good
`f` means choosing one whose reduction needs few XORs.

**The question left open in 2015.** Gustavo Banegas' master's thesis (LabSEC/UFSC,
2015) used a greedy XOR counter called **Conta-XOR** on all irreducible pentanomials of
some degrees and found two families with small counts:

| | Family | Status before this paper |
|---|---|---|
| first family  | `x^(2b+c) + x^(b+c) + x^b + x^c + 1` | analysed by Banegas, Custódio and Panario (J. Cryptographic Engineering, 2019): `3m − 2` XORs |
| **second family** | **`x^(b+2c) + x^(b+c) + x^b + x^c + 1`** | **left as future work in the thesis** |

**What the paper proves.** For every member of the second family (`m = b + 2c`,
`b > c ≥ 1`):

* a closed form for the quotient of the division by `f`, in terms of **comb sums** of
  stride `3c` (Theorem 7), and an explicit program, Algorithm 1, with **at most
  `3m − c − 3` XOR gates** and depth at most `⌊(m−2)/(3c)⌋ + 4` (Theorem 8,
  Proposition 9), plus a word-level version and a low-depth variant (Section VII);
* a second program, Algorithm 2 (the **chain construction**), with **exactly
  `3m − 3 − N(b,c)` XOR gates**, `N(b,c) ≈ (m − c)/3`, which is shorter whenever
  `b ≥ 4c + 1` (Theorem 13). The two constructions approach `8m/3` gates at opposite
  ends of the range of `c`;
* for members `f = G(x^γ)` built from five small base polynomials (`b/c = 3/2, 2, 3, 4, 5`),
  reduction splits into `γ` independent strips modulo `G`, and the optimal strip programs
  (proved with a SAT solver) give even shorter circuits (Proposition 4, Table 2).

**The idea in four steps.**

1. Long division by `f` gives a quotient `Q` and the remainder `R = D mod f`; the
   coefficients of `Q` satisfy a simple recurrence (Lemma 5).
2. For this family, `(x^c + 1)·f = x^(b+3c) + x^b + x^(2c) + 1` (Proposition 2). This
   identity makes the recurrence solvable.
3. The solution: each coefficient of `Q` is a sum of two comb sums `C_t`, where
   `C_t = h_t + h_(t+3c) + h_(t+6c) + ...` adds the high coefficients of `D` in steps of
   `3c` (Theorem 7).
4. Assemble the remainder `r_i = d_i + U_i + U_(i−b)` with `U = (1 + x^c)·Q`. Computing
   each comb sum once gives `3m − c − 3` gates (Theorem 8); building the sums
   `C_t + C_(t+c)` and `C_(k−c) + C_(k+c)` directly from each other, without comb sums,
   gives `3m − 3 − N(b,c)` (Theorem 13).

A small worked example, linked to the code, is in [docs/GUIDE.md](docs/GUIDE.md).

**Main numbers.**

| Degree | Best member of the second family | XORs (this paper) | First family | NIST pentanomial (Conta-XOR) |
|---|---|---|---|---|
| 163 | `x^163 + x^117 + x^71 + x^46 + 1` | **440** | 487 | 571 |
| 571 | `x^571 + x^389 + x^207 + x^182 + 1` | **1528** | 1711 | 2003 |

Over all degrees `5 ≤ m ≤ 1100`, the second family has irreducible members in 720
degrees; in all 405 degrees where both families have irreducible members it is cheaper,
by 9.7% on average. The chain construction improves the best member in 379 degrees.

---

## 2. Check everything

**Quick checks** (Python 3.10 or newer, nothing else, about 1 minute):

```bash
git clone https://github.com/rfcustodio/banegas-second-family-verification
cd banegas-second-family-verification
./run_quick_checks.sh            # or: make check
```

It prints one `PASS`/`ok` line per statement, on small degrees, ending with

```
ALL QUICK CHECKS PASSED
```

**Complete verification**, over all 201,117 members with `m ≤ 1100` as reported in the
paper, including the SAT results (gcc, Python 3, `pip install python-sat`, about 15
minutes):

```bash
make verify-all                  # runs verification/run_all.sh and compares with expected_output.txt
```

Both run automatically on GitHub after every push (tab **Actions**).

---

## 3. I want to check a specific statement

| I want to check... | Run | Time |
|---|---|---|
| Proposition 2, Lemma 5, Theorems 7 and 8, Proposition 9, Corollaries 10 and 16, Example 11 | `python3 checks/verify_statements.py` | 10 s |
| Lemma 12, Theorem 13, Example 14, Proposition 15 (chain construction) | `python3 checks/verify_chain.py` | 3 s |
| Tables 4, 8 and 9, Proposition 20, numbers of Section IX | `python3 checks/reproduce_tables.py` | 30 s |
| Observation 18 and Figure 2 (comparison with Conta-XOR) | `python3 checks/analyze_paar150.py` | 1 s |
| Table 6 (census up to degree 1100) and agreement of the two censuses | `python3 checks/compare_censuses.py` | 1 s |
| Table 7 (type I, type II and general pentanomials) | `python3 checks/compare_other_families.py` | 1 s |
| Table 10 (full multiplier and squaring) | `python3 checks/compare_multiplier.py` (recomputed by `python3 verification/multiplier.py`, 2 min) | 1 s |
| Lemma 19, equation (9), special members versus trinomials, word-level steps (added after the review) | `python3 checks/review_checks.py` | 45 s |
| Table 2 and Table 5 (SAT) | `cd verification && python3 exact_small.py && python3 exact_base.py && python3 compose_sat.py && python3 heuristic_small.py` | 2 min |
| Proposition 17 (low-depth variant) | `python3 generator/lowdepth.py --all 260` | 45 s |
| One particular polynomial, e.g. `b = 71, c = 46` | `python3 generator/fam2.py 71 46` (Algorithm 1), `python3 algorithm2/alg2prog.py 71 46` (Algorithm 2) | instant |
| The Conta-XOR count of any pentanomial | `python3 generator/contaxor.py 163 117 71 46` | instant |

The complete list, statement by statement, is in **[docs/CLAIMS.md](docs/CLAIMS.md)**.

---

## 4. Tour of the folders

```
.
├── README.md            this page
├── Makefile             shortcuts: make check | check-full | verify-all | figures | paper | data
├── run_quick_checks.sh  runs all quick checks
├── docs/                explanations: GUIDE, CLAIMS, WORKFLOW, GLOSSARY
├── paper/               the paper (LaTeX source in the IEEE Access template, figures, PDF)
├── generator/           code that produced the paper's numbers (Algorithm 1, strips, figures)
├── algorithm2/          the chain construction (Algorithm 2): generator, C verifier, census, MaxSAT
├── verification/        complete verification up to m = 1100 (C and Python, SAT models)
├── data/                raw results of the experiments
├── checks/              quick statement-by-statement checks (standard library only)
└── independent/         a second implementation, written separately (by Marcos)
```

Each folder has its own `README.md` explaining every file in it.

**Why several implementations?** `generator/` is the code used while writing the paper.
`verification/` re-implements every computation in C and Python and runs it over the
full range of the paper. `independent/` was written from the text of the paper alone,
without looking at `generator/`. For example, the two irreducibility censuses behind
Table 6 agree polynomial by polynomial (`checks/compare_censuses.py`).

**What the code proves and what it does not.** The scripts check the *statements* of
the theorems symbolically, so for all inputs, on every member up to `m = 1100`, and
recompute every published number. The SAT models prove optimality only for the small
instances of Tables 2 and 5. The *proofs* are in the paper and must be checked by
reading. Apart from those small instances there are no lower bounds: neither
`3m − c − 3` nor `3m − 3 − N(b,c)` is claimed to be optimal in general.

---

## 5. How we work together

* **Found a problem?** Open an *Issue*: say which statement, which command you ran and
  what it printed.
* **Want to change the paper or the code?** Create a branch, change, run
  `./run_quick_checks.sh`, and open a *Pull Request*. Details in
  [docs/WORKFLOW.md](docs/WORKFLOW.md).
* **Changed a number in the paper?** Update the expected value in the corresponding
  script and the line in `docs/CLAIMS.md`, so the checks keep guarding the text.

**History of corrections found by the checks**

| Date | Where | Problem | Fix |
|---|---|---|---|
| 2026-10-09 | Observation 18 (then 12), text | The draft said random tie-breaking "changed the outcome in only one case". | The data show 212 generic members improved (all with `b ≥ 6c`, by at most 12 XORs); only one of them reaches `3m − c − 3`. Text corrected. |
| 2026-11 | Table 2 | Strip programs found by the greedy search were reported for `f_{4,1}` and `f_{5,1}`. | SAT found shorter ones (`R1(f_{4,1}) = 15`; `R2, R1(f_{5,1}) = 16, 18`) and proved all values optimal. |
| 2026-11 | Section III | The coincidences of operands were said to explain all special savings. | They occur only for `b = 2c`; the text was rewritten. |

---

## Resumo em português

Este repositório reúne o artigo sobre a **segunda família de Banegas**
(`x^(b+2c) + x^(b+c) + x^b + x^c + 1`), o código e os dados que produziram os números
do artigo e scripts que verificam cada enunciado. Os resultados principais são duas
construções de redução: a forma fechada (Algoritmo 1), com no máximo `3m − c − 3` portas
XOR, e a construção em cadeias (Algoritmo 2), com exatamente `3m − 3 − N(b,c)` portas,
melhor sempre que `b ≥ 4c + 1`. Para os membros especiais, a decomposição em faixas
com programas ótimos (provados por SAT) dá custos ainda menores.

* **Verificação rápida:** `./run_quick_checks.sh` (Python 3.10+, cerca de 1 minuto).
* **Verificação completa até m = 1100:** `make verify-all` (gcc, Python 3 e `python-sat`,
  cerca de 15 minutos).
* **Verificar um enunciado específico:** veja a tabela da seção 3 ou
  [docs/CLAIMS.md](docs/CLAIMS.md).
* **Entender a matemática com um exemplo:** [docs/GUIDE.md](docs/GUIDE.md).
* **Propor mudanças:** abra uma *Issue* ou um *Pull Request*
  ([docs/WORKFLOW.md](docs/WORKFLOW.md)).
