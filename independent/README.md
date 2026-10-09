# `independent/`: independent verification suite

> This folder contains the original contents of the repository (first commit), moved
> here unchanged when the paper's own artifacts were added to `paper/`, `generator/`,
> `data/` and `checks/`. Run the commands below from inside this folder
> (`cd independent`), or prefix the script names with `independent/`.

This repository contains an **independent, from-scratch verification suite** for the
results in:

> M. Tomaszewski and R. F. Custódio, "Banegas' Second Family of Irreducible
> Pentanomials: a Closed-Form Reduction with 3m − c − 3 XOR Gates."

None of the code here reuses the paper's own symbolic generator or census scripts.
Everything was re-implemented from the paper's text (pseudocode, theorem statements,
and tables) and cross-checked against `contaxor.py`, a pentanomial-reduction toolkit
that was already extensively tested in an unrelated prior project — it serves as an
independent oracle, never as a copy of the paper's own code.

The purpose is reproducibility: if a second, independently-written implementation
reproduces every published number exactly, that is strong evidence against
implementation bugs on either side.

## What's in this repository

| File | What it checks | Paper section |
|---|---|---|
| `contaxor.py` | Dependency / oracle. Provides `matriz_reducao` (computes the true reduction matrix of any pentanomial by direct polynomial long division), `conta_xor` (the greedy "ContaXOR" algorithm from Banegas' thesis), and `eh_irredutivel` (Rabin irreducibility test). Not part of the paper's own contribution — this is pre-existing, independently-tested tooling used here as ground truth. | — |
| `second_family.py` | Algorithm 1 (the closed-form reduction program) and its low-depth variant (Corollary 10 / Proposition 11), both implemented literally from the published pseudocode, with inline comments mapping each line of Python to the corresponding pseudocode line. Verifies correctness (against `matriz_reducao`), exact XOR-gate count (3m − c − 3), and circuit depth. | Theorem 5, Theorem 6, Proposition 7, Corollary 10, Proposition 11 |
| `observacao12.py` | Reproduces the ContaXOR-vs-closed-form comparison, using the greedy algorithm (`conta_xor`) — a completely different code path from Algorithm 1 — for every pair with 5 ≤ m ≤ 150. | Observation 12, Section 7 |
| `censo_table3.py` | Independently recomputes the irreducibility census (which (b,c) pairs give irreducible polynomials, for both the first and second family, and which degrees have an irreducible trinomial) for 5 ≤ m ≤ 1100. Runs in resumable 100-degree blocks — safe to interrupt and rerun, it skips degrees already saved in the data file. | Table 3, Section 8 |
| `censo_table3_dados.json` | The actual output of `censo_table3.py` for all 1096 degrees (5–1100): which (b,c) pairs are irreducible in each family, and which degrees have an irreducible trinomial. Provided so the Table 3 numbers can be recomputed without re-running the (multi-hour) census. | Table 3, Section 8 |
| `table3_summary.py` | Loads `censo_table3_dados.json` and reduces it to the actual Table 3 summary numbers (member counts, degrees covered, cost comparisons between families, mean cost per bit). Runs in under a second. | Table 3, Section 8 |

## How to run

All scripts are plain Python 3 (3.10+, for `list[int]`-style type hints), no third-party
dependencies.

```bash
# Algorithm 1 + low-depth variant: worked example, NIST-degree table, special
# ratios, exhaustive check over all 14,850 members with m<=300, and a random
# fuzz test up to m=800.
python3 second_family.py

# ContaXOR vs. closed-form comparison (Observation 12), 5<=m<=150.
# Takes about 1-2 minutes.
python3 observacao12.py

# Irreducibility census (Table 3). Takes several hours in total; run in
# 100-degree blocks so progress is never lost. Already-computed degrees are
# skipped on rerun.
python3 censo_table3.py 5 100
python3 censo_table3.py 101 200
# ... continue up to:
python3 censo_table3.py 1001 1100

# Then recompute the Table 3 summary numbers (irreducible member counts,
# degrees covered, cost comparisons, mean cost per bit) from the saved JSON:
python3 table3_summary.py
```

## Results summary

Every number reproduced below is an exact match to the published value (no
rounding, no "close enough") unless noted otherwise.

**Algorithm 1 / closed form (`second_family.py`):**
- Paper's own worked example (degree 16, f₆,₅): 40 gates — exact match.
- All 8 members in Table 2 (NIST degrees 163, 233, 283, 409, 571): exact match on
  both gate count and depth.
- 450 "special ratio" members (b/c ∈ {3/2, 2, 3, 4, 5}): never longer than the
  formula, as the paper states can happen for these.
- Exhaustive check, all 14,850 members with m ≤ 300 (matches the number cited in
  the paper's abstract): 0 failures.
- Random fuzz, 300 pairs with m up to 800: 0 failures.
- Low-depth variant (Corollary 10 / Proposition 11): identical final output to
  the chain version in every case tested; paper's own example (m=571, c=22)
  reproduced exactly (chain: 1688 gates / depth 11; doubling: 2474 gates / depth 7).

**Observation 12 (`observacao12.py`), 5 ≤ m ≤ 150:**
- 3674 total pairs, 3541 generic — exact match.
- 879 members with b < 2c: all satisfy CX = 2m + 3c − 3 exactly.
- 1312 members with 2c < b < 6c: all satisfy CX = 3m − c − 3 exactly.
- 1350 members with b ≥ 6c: greedy is worse in 392 of them, by up to 112 gates
  — exact match.
- 110 cases where greedy beats the naive 3m−c−3 value: all 110 are special-ratio
  members, exactly as the paper's text anticipates (not a discrepancy).

**Table 3 census (`censo_table3.py`), 5 ≤ m ≤ 1100:**
- 1508 irreducible second-family members — exact match.
- 720 / 502 degrees with ≥1 second-/first-family member — exact match.
- 405 degrees with both families; second family cheaper in 403 (mean saving
  7.3%), first family cheaper only at m = 155, tied only at m = 5 — exact match.
- 502 degrees without an irreducible trinomial; 288 / 229 covered by second/first
  family, 112 covered by the second family only, 161 covered by neither — exact
  match.
- Mean cost per bit of the best generic second-family member: 2.77 — exact match.

## Scope and limitations

This is empirical, independent corroboration, not a substitute for the paper's own
mathematical proofs (Theorem 6 etc.). It covers every explicitly published number,
an exhaustive check up to m = 300, and random sampling up to m = 800 / m = 1100 —
it does not constitute a formal proof that Algorithm 1 is correct for all b > c ≥ 1.
