# A guided tour of the mathematics

This page explains the main result of the paper with one small example that you can
run. It follows the order of the paper (Sections 3 to 6) and points to the code that
implements each step. No previous knowledge of the code is needed.

**Running example:** `b = 9`, `c = 4`, so

    m = b + 2c = 17,   f(x) = x^17 + x^13 + x^9 + x^4 + 1   (irreducible).

```bash
python3 generator/fam2.py 9 4        # b=9 c=4 m=17: 44 XORs, depth 4, correct=True, 3m-c-3=44
python3 generator/contaxor.py 17 13 9 4   # the greedy (Conta-XOR) count for comparison: 44
```

---

## Step 0. What has to be computed

The product of two field elements is `D = d_0 + d_1 x + ... + d_32 x^32`
(degree `2m − 2 = 32`). We split it into a low part and a high part:

    D = L + x^17 · H,   L = d_0 + ... + d_16 x^16,   H = h_0 + ... + h_15 x^15,   h_s = d_(17+s).

The reduction must output the 17 bits `r_0, ..., r_16` of `R = D mod f`. Each `r_i` is the
XOR of some of the 33 input bits; which ones is fixed by `f` (the *reduction matrix*).
The question is how few 2-input XOR gates suffice.

## Step 1. Long division, written bit by bit (Lemma 3)

Write `D = Q·f + R`. The quotient `Q = q_0 + ... + q_15 x^15` has 16 bits. Comparing
coefficients gives two facts:

* (high part) `h_j = q_j + q_(j+c) + q_(j+2c) + q_(j+b+c)`, that is
  `h_j = q_j + q_(j+4) + q_(j+8) + q_(j+13)`;
* (low part) `r_i = d_i + q_i + q_(i−c) + q_(i−b) + q_(i−b−c)`.

The first fact determines `Q` from the top down, but using it directly costs about one
XOR per bit of `Q`. Checked by `check_lemma3` in `checks/verify_statements.py`.

## Step 2. The key identity (Proposition 2)

For every member of the family,

    (x^c + 1) · f(x) = x^(b+3c) + x^b + x^(2c) + 1.

Here: `(x^4 + 1)(x^17 + x^13 + x^9 + x^4 + 1) = x^21 + x^9 + x^8 + 1`. Six of the ten
terms cancel in pairs. This is what makes the recurrence of Step 1 solvable in closed
form: shifting the high part by `3c` can be undone at the price of two low terms.
Checked by `check_prop2`.

## Step 3. Comb sums and the closed-form quotient (Theorem 5)

Define the **comb sums**: add the high coefficients whose indices differ by multiples of
`3c = 12`,

    C_t = h_t + h_(t+12) + h_(t+24) + ...      (only indices up to n = m − 2 = 15)

In the example only four comb sums have more than one term:

    C_0 = h_0 + h_12    C_1 = h_1 + h_13    C_2 = h_2 + h_14    C_3 = h_3 + h_15

and `C_t = h_t` for `t ≥ 4`. Theorem 5 says that the quotient is simply

    q_j = C_j + C_(j+c) + h_(j+b+c)                       (equation 5)

and that `U = (1 + x^c)·Q`, the polynomial that appears in the remainder, is

    U_k = C_k + C_(k+c) + h_(k+b+c)     if k < c,
    U_k = C_(k−c) + C_(k+c) + h_(k+b)   if k ≥ c,         (equation 6)
    r_i = d_i + U_i + U_(i−b).                             (equation 7)

Each `U_k` is the sum of **two comb sums and at most one extra bit**. `check_thm5`
verifies (5), (6) and (7) symbolically for every member up to the chosen degree.

## Step 4. The program and its cost (Algorithm 1, Theorem 6)

Now compute each piece once and reuse it. In the example:

| Stage | Instructions | XORs |
|---|---|---|
| comb sums | `C_0 = h_0+h_12`, `C_1 = h_1+h_13`, `C_2 = h_2+h_14`, `C_3 = h_3+h_15` | `b − c − 1 = 4` |
| shared pairs | `Z_0 = C_0+h_13`, `Z_1 = C_1+h_14`, `Z_2 = C_2+h_15` | `c − 1 = 3` |
| the `U_k` | `U_0 = Z_0+C_4`, `U_1 = Z_1+C_5`, `U_2 = Z_2+C_6`, `U_3 = C_3+C_7`,<br>`U_4 = Z_0+C_8`, `U_5 = Z_1+C_9`, `U_6 = Z_2+C_10`, `U_7 = C_3+C_11`,<br>`U_8 = C_4+C_12`, `U_9 = C_5+C_13`, `U_10 = C_6+C_14`, `U_11 = C_7+C_15`;<br>`U_12..U_16 = C_8..C_12` (no gate) | `b + c − 1 = 12` |
| outputs | `r_i = d_i + U_i` for all 17 bits, plus `+ U_(i−9)` for `i ≥ 9` | `m + 2c = 25` |
| **total** | | **44 = 3m − c − 3** |

The "shared pairs" are the small trick that saves `c − 1` gates: `Z_i` is used by both
`U_i` and `U_(i+c)`.

In the code, the four stages are the four loops of `program()` in
`generator/fam2.py`. Every intermediate value is stored as a *linear form* (a bit mask
saying which inputs `d_j` it adds). At the end the 17 output forms are compared with the
17 rows of the reduction matrix of `f`; if they are equal, the program is correct for
**all** inputs. This is why the checks are exact and not statistical.

## Step 5. Depth and the word-level version (Proposition 7, Corollary 10, Proposition 11)

* **Depth.** The comb sums are chains of length about `m/(3c)`; everything else adds at
  most 4 levels. In the example the depth is 4.
* **Software.** The same formulas on whole bit vectors:

  ```python
  C = H ^ (H >> 3c) ^ (H >> 6c) ^ ...        # comb sums (or by doubling)
  Q = C ^ (C >> c) ^ (H >> (b + c))          # quotient, equation (5)
  U = Q ^ (Q << c)
  R = (L ^ U ^ (U << b)) mod x^m             # equation (7)
  ```

  See `generator/wordlevel.py`; about six shift-and-XOR operations when `b ≤ 4c + 1`.
* **Low depth.** Computing the comb sums by doubling gives logarithmic depth at the cost
  of a few more gates (`generator/lowdepth.py`).

## Step 6. How this compares with the greedy count (Section 7)

The greedy counter of the thesis (Conta-XOR) finds the same `3m − c − 3` when
`2c < b < 6c`, as in our example (44). When `b < 2c` it needs exactly `2c − b` more
gates; when `b ≥ 6c` it sometimes needs more as well. Try:

```bash
python3 generator/fam2.py 71 46               # 440 (degree 163, b < 2c)
python3 generator/contaxor.py 163 117 71 46   # 461 = 440 + (2·46 − 71)
```

The full comparison over 3,541 members is reproduced by `checks/analyze_paar150.py`.
