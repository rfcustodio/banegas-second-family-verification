# `data/sat/`: evidence for the SAT results (Tables 2 and 5)

| File | Content |
|---|---|
| `programs.json` | The program found at the stated number of gates for each instance: 11 members of Table 5 (`f_b_c`) and the 5 strip programs `R1` of Table 2 (`R1_f_b_c`). Gates are written `t = u ^ v`; inputs `d0, d1, ...` are the coefficients of the dividend; each output `r_i = d_i ^ ...`. |
| `*_K<k>.cnf.gz` | DIMACS CNF (gzip) stating that `R'` has a program with `k - (number of outputs)` gates, so that the complete reduction would need `k` gates, one less than the stated optimum. All 12 are unsatisfiable. |
| `evidence.json` | Per instance: sizes, CNF variables and clauses, SHA-256 of each CNF and of its DRAT proof, solver times, tool versions, and the drat-trim verdict. |

**Encoding.** `verification/slp_sat.py`, function `encode` (one-hot operand selection,
operand indices ordered, one output literal per target), following Stoffelen's encoding.
Targets of weight 1 and repeated targets need no gate. A program with fewer gates can
always be padded with unused gates, so unsatisfiability at `k` rules out every program with
at most `k` gates. The reduction to `R'` is Lemma 19 of the paper; `sat_evidence.py`
checks its hypothesis (no zero row) for every instance, including the strip matrices.

**Tools.** Programs: PySAT 1.9.dev21, solver `Cadical153` (CaDiCaL 1.5.3).
Certificates: CaDiCaL 3.0.1 (github.com/arminbiere/cadical, commit `c607304`) with
`--no-binary`, checked with drat-trim (github.com/marijnheule/drat-trim, commit `2e3b2dc`).

**Checking.**

* `python3 checks/verify_sat_programs.py` (standard library, 1 s): evaluates every program
  symbolically against the reduction matrix, checks the gate counts against the paper and the
  CNF hashes. Part of `./run_quick_checks.sh`. The line "DRAT s VERIFIED" that it prints is the
  verdict recorded in `evidence.json`; this script does not run drat-trim.
* `verification/check_sat_proofs.sh PROOF_DIR DRAT_TRIM` (about 2 min): checks the 12 DRAT
  proofs. The proofs (46 MB compressed, up to 113 MB each uncompressed) are not in git; take
  them from the release asset `sat-proofs-v22.tar`, or let the script regenerate them with
  `CADICAL=/path/to/cadical` (CaDiCaL is deterministic: the regenerated proofs have the
  recorded hashes). `make sat-proofs` builds both tools at the recorded commits and runs the
  regeneration and the check.
* `python3 verification/sat_evidence.py CADICAL DRAT_TRIM` (about 8 min) rebuilds this
  directory from scratch.
