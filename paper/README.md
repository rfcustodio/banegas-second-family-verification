# `paper/`: the paper

| File | Content |
|---|---|
| `main.tex` | LaTeX source in the IEEE Access template (a copy of the Overleaf master). |
| `refs.bib` | Bibliography (BibTeX, style `IEEEtran`). |
| `main.pdf` | Compiled paper (17 pages). |
| `ieeeaccess.cls`, `IEEEtran.cls`, `logo.png`, `notaglinelogo.png`, `bullet.png` | IEEE Access template files (do not edit). |
| `fig_comb.pdf`, `fig_comb.tex` | Figure 1 (comb sums) and its TikZ source (`pdflatex fig_comb`). |
| `fig_gain.pdf` | Figure 2: greedy count minus closed form; made by `generator/make_figures.py` from `data/paar150.txt`. |
| `fig_census.pdf` | Figure 3: cost per bit by degree, with both constructions; made by `generator/make_figures.py` from `data/census_alg2.json`. |
| `*.jpg` | Author photographs for the biographies. |

**Compile** (any TeX Live or MacTeX):

```bash
cd paper
pdflatex main && bibtex main && pdflatex main && pdflatex main
```

or `make paper` from the repository root.

**Numbering.** Theorems, propositions, lemmas, corollaries, definitions, examples and
observations share one counter. `docs/CLAIMS.md` uses the numbers of the compiled PDF:
Def. 1, Prop. 2, Def. 3, Prop. 4, Lemma 5, Def. 6, Thm. 7, Thm. 8, Prop. 9, Cor. 10,
Ex. 11, Lemma 12, Thm. 13, Ex. 14, Prop. 15, Cor. 16, Prop. 17, Obs. 18, Prop. 19.
Sections are numbered I to X. If the text changes and the numbering moves, update
`CLAIMS.md` and the labels printed by the scripts.
