# `checks/`: statement-by-statement verification

These scripts check the paper. They use only the Python standard library (Python 3.10+)
and print, for every item, the value they computed next to the value in the paper.
Each exits with status 0 if everything matches and 1 otherwise, so they can be used in
automated tests.

| Script | Checks | Time |
|---|---|---|
| `verify_statements.py` | Proposition 2 (i)-(v); Lemma 3 (random products against long division); Theorem 5 (equations 5, 6, 7, symbolically for every member); Theorem 6 and Proposition 7 (via `generator/fam2.py`, including the measured-depth statistic of Section 5); Corollary 8 (complete multiplier on random field elements); Example 9; Corollary 10. Option `--mmax M` sets the largest degree (default 120; the paper uses 300). | 10 s (default), 3 min (`--mmax 300`) |
| `reproduce_tables.py` | Every entry of Table 2 and Table 4, and the numbers quoted in Section 8. | 1 s |
| `analyze_paar150.py` | Every number of Observation 12 and the content of Figure 2, from `data/paar150.txt`. | 1 s |
| `compare_censuses.py` | Compares, polynomial by polynomial, the authors' census (`data/`) with the independent census (`independent/censo_table3_dados.json`), then recomputes Table 3. | 1 s |

To run all of them: `./run_quick_checks.sh` from the repository root.
