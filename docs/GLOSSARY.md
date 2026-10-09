# Glossary

Terms used in the paper and in the code, in alphabetical order. Names used in the
Portuguese code are given in parentheses.

**Algorithm 1.** The reduction program of the paper for the second family. Implemented
in `generator/fam2.py` and, independently, in `independent/second_family.py`.

**BCP family / first family.** `x^(2b+c) + x^(b+c) + x^b + x^c + 1`, studied by Banegas,
Custódio and Panario (2019), with reduction cost `3m − 2` (and `12m/5 − 1` when `b = 2c`).

**Boyar–Peralta heuristic (BP).** A literature heuristic for short XOR programs that, unlike
the greedy algorithm, may use cancellations (`a ⊕ a = 0`). Used only for small degrees
(`generator/smallm.py`).

**Comb sum `C_t`.** `C_t = h_t + h_(t+3c) + h_(t+6c) + ...`, the sum of the high
coefficients whose index is `t` plus a multiple of `3c`. The building block of
Theorem 5.

**Conta-XOR (`CX`).** The greedy XOR counter of Banegas' thesis: repeatedly replace the
most frequent pair of operands by a new variable. Implemented in
`generator/contaxor.py` (Python), `generator/xorred.c` (C) and
`independent/contaxor.py`. Ties between equally frequent pairs are broken by taking the
lexicographically smallest pair.

**Depth.** The longest chain of XOR gates from an input to an output; it determines the
delay of a hardware circuit. (`profundidade`)

**`dXOR` (direct count).** Cost of adding every output from scratch: the sum over the
rows of the reduction matrix of (row weight − 1).

**Generic / special member.** A member is *special* if `b/c` is `3/2, 2, 3, 4` or `5`;
then `f(x) = G(x^g)` with a very short `G` and the greedy algorithm can beat the closed
form. All others are *generic*. `b = 2c` is the equally spaced pentanomial.

**`h_s`.** High coefficients of the product: `h_s = d_(m+s)`, `0 ≤ s ≤ n = m − 2`.

**Irreducible.** A polynomial with no non-trivial factor over `GF(2)`; only irreducible
`f` define a field. Tested with Rabin's test (`irredutivel`, `eh_irredutivel`).

**Linear form / symbolic verification.** Every signal of an XOR program is the XOR of a
set of inputs; the code stores that set as an integer bit mask. Two programs are equal
for all inputs iff their output forms are equal, so comparing forms with the rows of the
reduction matrix is a proof of correctness for that `(b, c)`.

**Member.** A pair `(b, c)` with `b > c ≥ 1`, giving the pentanomial `f_{b,c}` of degree
`m = b + 2c`. Pairs are listed in `data/` as `m b c`.

**NIST degrees.** 163, 233, 283, 409 and 571, the degrees of the binary fields of the
former NIST elliptic curves (now deprecated by NIST SP 800-186).

**`Q`, `U`, `Z`.** `Q` is the quotient of the division of the product by `f`;
`U = (1 + x^c)·Q`; `Z_i = C_i + h_(i+b+c)` are the pairs shared by `U_i` and `U_(i+c)`.

**Random tie-breaking (`RG` in `data/paar150.txt`).** The greedy algorithm run 20 more
times choosing randomly among equally frequent pairs; the best value is kept.

**Reduction matrix.** The `m × (2m − 1)` bit matrix whose column `j` contains
`x^j mod f`; row `i` lists the inputs that are added to produce output bit `r_i`
(`matriz_reducao`).

**Second family.** `f_{b,c} = x^(b+2c) + x^(b+c) + x^b + x^c + 1`, the subject of the paper.

**XOR count / gates.** Number of 2-input XOR instructions of a program (`portas`).
