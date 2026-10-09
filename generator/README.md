# `generator/`: the code that produced the paper's numbers

All Python scripts run with Python 3.10+ and the standard library, except where noted.
Run them from the repository root, e.g. `python3 generator/fam2.py 71 46`.

| File | What it does | Paper | Example |
|---|---|---|---|
| `fam2.py` | **Algorithm 1.** Builds the reduction program for `f_{b,c}` and verifies it symbolically against the reduction matrix (correct for all inputs). Prints gate count, depth, correctness and `3m − c − 3`. | Thm. 6, Prop. 7, Ex. 9 | `python3 generator/fam2.py 71 46` |
| `lowdepth.py` | Low-depth variant: comb sums by doubling. `--all M` checks the gate and depth bounds of Prop. 11 for every member with `m < M`. | Prop. 11 | `python3 generator/lowdepth.py 527 22` |
| `wordlevel.py` | Word-level reduction (shifts and XORs on whole bit vectors), tested on 10,000 random products. | Cor. 10 | `python3 generator/wordlevel.py 207 182` |
| `contaxor.py` | Conta-XOR, the greedy counter of Banegas' thesis, for any polynomial; prints irreducibility, `dXOR`, the greedy count and depth, and verifies the program by simulation. Options: `-r K` adds `K` runs with random tie-breaking, `-p` prints the program. | baseline `CX` (Sec. 7, Tables 2, 4) | `python3 generator/contaxor.py 163 117 71 46 -r 20` |
| `xorred.c` | Fast C version of the greedy counter and of the irreducibility test; also produces the censuses. See the modes below. | `data/` | see below |
| `smallm.py` | Small degrees: greedy count, greedy over all tie-breaking sequences, and the Boyar–Peralta heuristic (with cancellations). Needs `numpy`. Arguments: `m a b c runs`. | Sec. 7 "Small degrees" | `python3 generator/smallm.py 10 7 4 3 10` |
| `sat.py` | SAT question "is there a program with `k` gates?". Needs `python-sat`. Exploratory; not used for any statement of the paper. | - | `python3 generator/sat.py 7 5 3 2 15` |
| `make_figures.py` | Regenerates Figures 2 and 3 into `paper/` from `data/`. Needs `numpy`, `matplotlib`. | Figs. 2, 3 | `python3 generator/make_figures.py` |

## `xorred.c` modes

```bash
gcc -O2 -o xorred generator/xorred.c
./xorred one 163 117 71 46 20 1    # one pentanomial m a b c, K=20 random runs, seed 1
./xorred list 20 5 < pairs.txt     # many pentanomials, one "m a b c" per line
./xorred fam2 5 1100               # irreducible members of the second family
./xorred fam1 5 1100               # irreducible members of the first family
./xorred tri 2 1100                # smallest irreducible trinomial per degree
```

Output columns of `one` and `list`: `m a b c dXOR CX depth_CX RG depth_RG`.
