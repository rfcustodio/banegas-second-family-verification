# Banegas' second family of irreducible pentanomials

**Working repository of the paper**

> M. Tomaszewski and R. F. Custódio,
> *Banegas' Second Family of Irreducible Pentanomials: a Closed-Form Reduction with
> 3m − c − 3 XOR Gates* (draft, LabSEC/UFSC).

This repository holds the paper, all the code and data behind it, and scripts that
check every statement of the paper. It is meant for the co-authors: to read the paper,
reproduce each number, find mistakes and improve the text.

**Start here:** [1. What the paper is about](#1-what-the-paper-is-about) ·
[2. Check everything in one command](#2-check-everything-in-one-command) ·
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
`b > c ≥ 1`) the reduction can be done with

> **at most `3m − c − 3` XOR gates** (Theorem 6),

with an explicit, uniform program (Algorithm 1), small depth (Proposition 7), a
word-level version for software (Corollary 10) and a low-depth variant
(Proposition 11).

**The idea in four steps.**

1. Long division by `f` gives a quotient `Q` and the remainder `R = D mod f`; the
   coefficients of `Q` satisfy a simple recurrence (Lemma 3).
2. For this family, `(x^c + 1)·f = x^(b+3c) + x^b + x^(2c) + 1` (Proposition 2). This
   identity makes the recurrence solvable.
3. The solution: each coefficient of `Q` is a sum of two **comb sums** `C_t`, where
   `C_t = h_t + h_(t+3c) + h_(t+6c) + ...` adds the high coefficients of `D` in steps of
   `3c` (Theorem 5).
4. Compute each comb sum once, reuse it, and assemble the remainder:
   `r_i = d_i + U_i + U_(i−b)` with `U = (1 + x^c)·Q`. Counting the gates gives
   `3m − c − 3` (Theorem 6).

A small worked example (degree 16), linked to the code line by line, is in
[docs/GUIDE.md](docs/GUIDE.md).

**Main numbers.**

| Degree | Best member of the second family | XORs (this paper) | First family | NIST pentanomial (Conta-XOR) |
|---|---|---|---|---|
| 163 | `x^163 + x^117 + x^71 + x^46 + 1` | **440** | 487 | 571 |
| 571 | `x^571 + x^389 + x^207 + x^182 + 1` | **1528** | 1711 | 2003 |

Over all degrees `5 ≤ m ≤ 1100`, the second family has irreducible members in 720
degrees, and where both families exist it is cheaper in 403 of 405 degrees.

---

## 2. Check everything in one command

You need **Python 3.10 or newer** and nothing else.

```bash
git clone <this repository>
cd banegas-second-family-verification
./run_quick_checks.sh            # or: make check
```

It takes about 15 seconds and prints one `PASS`/`FAIL` line per statement, ending with

```
ALL QUICK CHECKS PASSED
```

For the full range used in the paper (all members up to `m = 300`, about 3 minutes):

```bash
make check-full
```

The same checks run automatically on GitHub after every push (tab **Actions**).

---

## 3. I want to check a specific statement

| I want to check... | Run | Time |
|---|---|---|
| Proposition 2, Lemma 3, Theorem 5, Theorem 6, Proposition 7, Corollaries 8 and 10, Example 9 | `python3 checks/verify_statements.py` | 10 s |
| Table 2 and Table 4, and the numbers in Section 8 | `python3 checks/reproduce_tables.py` | 1 s |
| Observation 12 and Figure 2 (comparison with Conta-XOR) | `python3 checks/analyze_paar150.py` | 1 s |
| Table 3 (census up to degree 1100) and agreement of the two censuses | `python3 checks/compare_censuses.py` | 1 s |
| Proposition 11 (low-depth variant) | `python3 generator/lowdepth.py --all 260` | 45 s |
| One particular polynomial, e.g. `b = 71, c = 46` | `python3 generator/fam2.py 71 46` | instant |
| The Conta-XOR count of any pentanomial | `python3 generator/contaxor.py 163 117 71 46` | instant |

The complete list, statement by statement, with the result of the last run, is in
**[docs/CLAIMS.md](docs/CLAIMS.md)**.

---

## 4. Tour of the folders

```
.
├── README.md            this page
├── Makefile             shortcuts: make check | check-full | figures | paper | data
├── run_quick_checks.sh  runs all fast checks
├── docs/                explanations for the co-authors
│   ├── GUIDE.md         the mathematics in plain words, with a worked example
│   ├── CLAIMS.md        every statement of the paper -> script that checks it
│   ├── WORKFLOW.md      how to propose changes, rerun checks, rebuild the paper
│   └── GLOSSARY.md      terms used in the paper and in the code
├── paper/               the paper (LaTeX source, bibliography, figures, PDF)
├── generator/           the code that produced the paper's numbers
├── data/                raw results of the experiments
├── checks/              scripts that verify the paper, statement by statement
└── independent/         a second implementation, written separately (by Marcos)
```

Each folder has its own `README.md` explaining every file in it.

**Why two implementations?** `generator/` is the code used while writing the paper.
`independent/` was written afterwards from the text of the paper alone, without looking
at `generator/`. When two separately written programs give the same numbers, a bug in
either of them becomes very unlikely. For example, the two irreducibility censuses
behind Table 3 agree polynomial by polynomial (`checks/compare_censuses.py`).

**What the code proves and what it does not.** The scripts check the *statements* of
the theorems on every member up to `m = 300` (symbolically, so for all inputs) and on
random products; they recompute every published number. The *proofs* are in the paper
and must be checked by reading. Nothing here is a lower bound: the paper does not claim
that `3m − c − 3` is optimal.

---

## 5. How we work together

* **Found a problem?** Open an *Issue*: say which statement, which command you ran and
  what it printed.
* **Want to change the paper or the code?** Create a branch, change, run
  `./run_quick_checks.sh`, and open a *Pull Request*. Details in
  [docs/WORKFLOW.md](docs/WORKFLOW.md).
* **Changed a number in the paper?** Update the expected value in the corresponding
  script in `checks/` and the line in `docs/CLAIMS.md`, so the checks keep guarding the
  text.

**History of corrections found by the checks**

| Date | Where | Problem | Fix |
|---|---|---|---|
| 2026-10-09 | Observation 12, text | The draft said random tie-breaking "changed the outcome in only one case". | The data show 212 generic members improved (all with `b ≥ 6c`, by at most 12 XORs); only one of them reaches `3m − c − 3`. Text corrected. |

---

## Resumo em português

Este repositório reúne o artigo sobre a **segunda família de Banegas**
(`x^(b+2c) + x^(b+c) + x^b + x^c + 1`), o código e os dados que produziram os números
do artigo e scripts que verificam cada enunciado. O resultado principal é uma redução
com no máximo `3m − c − 3` portas XOR para todos os membros da família.

* **Verificar tudo:** `./run_quick_checks.sh` (Python 3.10+, cerca de 15 s).
* **Verificar um enunciado específico:** veja a tabela da seção 3 ou
  [docs/CLAIMS.md](docs/CLAIMS.md).
* **Entender a matemática com um exemplo:** [docs/GUIDE.md](docs/GUIDE.md).
* **Propor mudanças:** abra uma *Issue* ou um *Pull Request*
  ([docs/WORKFLOW.md](docs/WORKFLOW.md)).

A pasta `independent/` contém a implementação independente do Marcos; `generator/`
contém o código usado na redação. As duas concordam em todos os números publicados.
