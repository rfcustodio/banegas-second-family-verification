# `checks/`: statement-by-statement verification

These scripts check the paper. They use only the Python standard library (Python 3.10+)
and print, for every item, the value they computed next to the value in the paper.
Each exits with status 0 if everything matches and 1 otherwise, so they can be used in
automated tests.

| Script | Checks | Time |
|---|---|---|
| `verify_statements.py` | Proposition 2 (i)-(v); Lemma 5 (random products against long division); Theorem 7 (equations 5, 6, 7, symbolically for every member); Theorem 8 and Proposition 9 (via `generator/fam2.py`, including the measured-depth statistic of Section V); Corollary 10 (complete multiplier on random field elements); Example 11; Corollary 16. Option `--mmax M` sets the largest degree (default 120; the paper uses 300). | 10 s (default), 3 min (`--mmax 300`) |
| `verify_chain.py` | Lemma 12, Theorem 13 (Algorithm 2 symbolically, exactly `3m-3-N(b,c)` gates), the formula and the cases of `N(b,c)`, Proposition 15, Example 14, the last column of Table 4 and the values of Section VI. Option `--mmax M` (default 120). | 3 s |
| `reproduce_tables.py` | Every entry of Tables 4, 7 and 8, Proposition 19 against the census, and the numbers quoted in Section IX. | 30 s |
| `analyze_paar150.py` | Every number of Observation 18 and the content of Figure 2, from `data/paar150.txt`. | 1 s |
| `compare_censuses.py` | Compares, polynomial by polynomial, the authors' census (`data/`) with the independent census (`independent/censo_table3_dados.json`), then recomputes Table 6 and the census numbers of Section IX with both constructions. | 1 s |

To run all of them: `./run_quick_checks.sh` from the repository root.

The complete verification up to `m = 1100`, including the SAT results of Tables 2 and 5,
is in `verification/` (`make verify-all`).
