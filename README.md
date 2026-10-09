# Banegas' second family of irreducible pentanomials: paper, code and verification

This repository gathers everything behind the paper

> M. Tomaszewski and R. F. Custódio, *Banegas' Second Family of Irreducible
> Pentanomials: a Closed-Form Reduction with 3m − c − 3 XOR Gates* (draft).

The paper studies the pentanomials

    f(x) = x^(b+2c) + x^(b+c) + x^b + x^c + 1,   m = b + 2c,   b > c >= 1,

the "second family" found by G. Banegas in his master's thesis (LabSEC/UFSC, 2015) and
left there as future work. Its main result is an explicit reduction program modulo `f`
with at most `3m − c − 3` XOR gates (Theorem 6), built from a closed form of the
quotient of the division by `f` (Theorem 5).

The goal of the repository is that every co-author and reviewer can **check every
statement of the paper** by running code, and see which code and which data produced
each number.

## Layout

```
paper/        LaTeX source, bibliography, figures and compiled PDF of the paper
generator/    the authors' code that produced the numbers of the paper
data/         raw outputs of the experiments (greedy counts, irreducibility censuses)
checks/       scripts that verify the statements of the paper, one by one
independent/  an independent, from-scratch re-implementation (written separately)
CLAIMS.md     map: each theorem, table, figure and number -> how it is verified
run_quick_checks.sh   runs all fast checks (about 15 seconds)
```

Two code bases are kept on purpose. `generator/` is the code used while writing the
paper. `independent/` was written afterwards, from the text of the paper only, without
reusing `generator/`. When both reproduce the same number, an implementation bug on
either side becomes very unlikely. `checks/compare_censuses.py` compares their outputs
directly.

## Quick start

Requirements: Python 3.10 or newer. The checks in `checks/` and the scripts in
`independent/` need no third-party packages. Optional: `gcc` for `generator/xorred.c`,
`numpy` for the Boyar-Peralta experiment, `numpy` and `matplotlib` for the figures,
`python-sat` for the SAT experiment, and a LaTeX installation with `biblatex` to compile
the paper.

```bash
./run_quick_checks.sh          # all fast checks; prints PASS/FAIL per statement
```

or step by step:

```bash
python3 checks/verify_statements.py            # Prop. 2, Lemma 3, Thm. 5, Thm. 6, Prop. 7,
                                               # Cor. 8, Example 9, Cor. 10 (m <= 120, ~10 s)
python3 checks/verify_statements.py --mmax 300 # same, over the range used in the paper (~2.5 min)
python3 checks/reproduce_tables.py             # Table 2, Table 4 (~1 s)
python3 checks/analyze_paar150.py              # Observation 12, Figure 2 (from data/)
python3 checks/compare_censuses.py             # Table 3; authors' census vs independent census
python3 generator/lowdepth.py --all 260        # Proposition 11 (~45 s)
```

## What each folder contains

### `paper/`

| File | Content |
|---|---|
| `artigo2.tex` | LaTeX source of the paper (biblatex, `backend=bibtex`). |
| `refs.bib` | Bibliography. |
| `fig_gain.pdf` | Figure 2, produced by `generator/make_figures.py` from `data/paar150.txt`. |
| `fig_census.pdf` | Figure 3, produced by `generator/make_figures.py` from `data/census.json`. |
| `artigo2.pdf` | Compiled paper. Compile with `pdflatex artigo2; bibtex artigo2; pdflatex artigo2; pdflatex artigo2`. |

Figure 1 (comb sums) is drawn in TikZ inside `artigo2.tex`.

### `generator/` (authors' code)

| File | What it does | Paper |
|---|---|---|
| `fam2.py` | Algorithm 1. Builds the reduction program for any `(b, c)`; every signal is an `F2`-linear form in the inputs `d_0..d_{2m-2}` (a Python integer used as a bit mask), so comparing the outputs with the rows of the reduction matrix proves correctness for **all** inputs, not only for test vectors. Reports gate count and depth. `python3 generator/fam2.py b c` | Thm. 6, Prop. 7, Ex. 9 |
| `lowdepth.py` | Low-depth variant (comb sums by doubling). `python3 generator/lowdepth.py b c` or `--all M` | Prop. 11 |
| `wordlevel.py` | Word-level reduction with shifts and XORs on whole polynomials, tested against polynomial division. `python3 generator/wordlevel.py b c` | Cor. 10 |
| `contaxor.py` | Conta-XOR (greedy XOR counting of Banegas' thesis) in Python, with Rabin irreducibility test and verification of the produced program by simulation. `python3 generator/contaxor.py m a b c [-r K] [-p]` | baseline `CX` in Sec. 7, Tables 2 and 4 |
| `xorred.c` | Fast C implementation of the same greedy counter (lexicographic and random tie-breaking), of the irreducibility test, and of the censuses. Compile with `gcc -O2 -o xorred generator/xorred.c`. Modes: `one m a b c K seed`, `list K seed < file`, `fam2 m0 m1`, `fam1 m0 m1`, `tri m0 m1`, `irr m amax`. | `data/` files |
| `smallm.py` | Small degrees: greedy with all tie-breaking sequences, and the Boyar-Peralta heuristic (needs `numpy`). `python3 generator/smallm.py 9 7 5 2 10` | Sec. 7, "Small degrees" |
| `sat.py` | SAT encoding of "is there an XOR program with k gates?" (needs `python-sat`). `python3 generator/sat.py 7 5 3 2 15` | exploratory, not used in the paper |
| `make_figures.py` | Regenerates Figures 2 and 3 into `paper/`. | Figs. 2, 3 |

### `data/` (raw experiment outputs)

See `data/README.md` for the exact format of each file and the command that produced it.

| File | Content |
|---|---|
| `paar150.txt` | Greedy counts for all 3,674 members with `5 <= m <= 150`. |
| `fam2_irr.txt` | All irreducible members of the second family, `5 <= m <= 1100` (1,508 lines). |
| `fam1_irr.txt` | All irreducible members of the first family (BCP), `5 <= m <= 1100`. |
| `tri.txt` | For each degree with an irreducible trinomial, the smallest such `k`. |
| `census.json` | Best member per degree for each family, used by Figure 3. |

### `checks/` (statement-by-statement verification)

| Script | Verifies |
|---|---|
| `verify_statements.py` | Proposition 2 (i)-(v); Lemma 3 (random products against long division); Theorem 5 (closed forms (5), (6), (7), symbolically, for every member in range); Theorem 6 and Proposition 7 (via `generator/fam2.py`); Corollary 8 (a full schoolbook multiplier, random field products); Example 9; Corollary 10. |
| `reproduce_tables.py` | Every entry of Tables 2 and 4: irreducibility, `dXOR`, Conta-XOR, gate count and depth of Algorithm 1, and the best member of each family at the NIST degrees. |
| `analyze_paar150.py` | Every number of Observation 12 and the content of Figure 2, from `data/paar150.txt`. |
| `compare_censuses.py` | The authors' census (`data/`) against the independent census (`independent/censo_table3_dados.json`), member by member; then all numbers of Table 3. |

### `independent/`

The independent suite written separately from the paper's code; see
`independent/README.md`. It re-implements Algorithm 1, the low-depth variant, the
Conta-XOR comparison of Observation 12 and the census of Table 3.

## Status of the last full run

All checks pass. The verification found one wording error in the first draft, already
corrected in `paper/artigo2.tex` (see `CLAIMS.md`, Observation 12): randomised
tie-breaking improved the greedy count in 212 generic members, not in one; it closed the
gap to `3m − c − 3` in only one of them.

## Scope

The theorems are proved in the paper; the code checks the proofs' statements on all
members up to `m = 300` (symbolically) and on random products up to `m = 300`, and
re-derives every published number. It does not replace the proofs. The censuses cover
`5 <= m <= 1100`. Statements about optimality are not made in the paper, and nothing
here should be read as a lower bound.

## Contributing

Please open an issue for any discrepancy between a number in the paper and the output of
a script, quoting the command and its output. When the paper changes, update
`CLAIMS.md` and rerun `./run_quick_checks.sh` before committing.
