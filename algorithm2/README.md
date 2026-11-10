# Chain construction (Algorithm 2, Theorem 13)

Code for Section VI of the paper. The chain construction computes the reduction modulo
f = x^m + x^{b+c} + x^b + x^c + 1 (m = b+2c) with exactly

    3m - 3 - N(b,c),   N(b,c) = #{1 <= u <= b+c-1 : floor(u/c) = 2 (mod 3)}
                              = c*floor((b+c)/3c) + max(0, (b+c) mod 3c - 2c)

XOR gates. It is shorter than the closed form 3m-c-3 (Algorithm 1) exactly when b >= 4c+1,
equal for 2c <= b <= 4c, and longer for b < 2c.

It uses the sums E_t = C_t + C_{t+c} and P_k = C_{k-c} + C_{k+c} of the comb sums C_t and the
identities (Lemma 12)

    E_t = h_t + P_{t+2c},   P_k = h_{k-c} + E_{k+c},   P_k = E_{k-c} + E_k,

so that no comb sum is ever computed. All shifts are multiples of c, and the reduction splits
into c independent chains.

## Files

| File | Content |
|---|---|
| `alg2prog.py` | Algorithm 2 exactly as in the paper: `python3 alg2prog.py b c [p]` builds the program, checks it symbolically and prints (correct, gates, 3m-3-N, depth); with a third argument it also lists the gates. |
| `alg2verify.c` | Symbolic verification of Algorithm 2 for all 201,117 members with m <= 1100: correctness, gate count 3m-3-N, closed formula for N, depth bound 2*floor((n-c)/3c)+6, and the condition b >= 4c+1 for an improvement. |
| `census_alg2.py` | Census of Section IX with both constructions (Table 6, special-member table, NIST degrees). Needs `sec.txt`, `fst.txt`, `tri.txt` from `../verification` (run `run_all.sh` first); writes `data/census_alg2.json`. |
| `fig_census.py` | Figure 3 (`paper/fig_census.pdf`) from `data/census_alg2.json`. |
| `chain2.py` | Weighted MaxSAT model (pysat RC2) of one chain, with comb sums, E, P, the shared pairs Z and all identities of Lemma 12 and Theorem 7. `solve(J, 'A' or 'B')` returns the optimum. |
| `chaincheck.py` | Confirms that the MaxSAT optimum equals the cost of Algorithm 2 on each chain for every chain length J <= 1100 (except J = 2 in the first c-1 classes, which only occurs when b < 2c). Slow (several minutes). |

## Expected output

    $ gcc -O2 -o alg2verify alg2verify.c && ./alg2verify 4 1100 527 22
    INFO b=527 c=22 gates=1534 depth=20
    SUMMARY m=[4,1100] pairs=201117 failures=0 improved=100284 worse=50142 max(depth-bound)=-1
    $ python3 alg2prog.py 8 1
    (True, 24, 24, 6)
    $ python3 chaincheck.py
    checked J<=1100, mismatches: 0

`run_all.sh` in `../verification` runs everything except `chaincheck.py`.
Requirements: gcc, Python 3, `python-sat` (`pip install python-sat`) for the MaxSAT model.
