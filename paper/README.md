# `paper/`: the paper

| File | Content |
|---|---|
| `artigo2.tex` | LaTeX source (single file). Bibliography with `biblatex`, `backend=bibtex`. |
| `refs.bib` | Bibliography entries (only the cited ones are printed). |
| `artigo2.pdf` | Compiled paper (12 pages). |
| `fig_gain.pdf` | Figure 2: greedy count minus closed form; made by `generator/make_figures.py` from `data/paar150.txt`. |
| `fig_census.pdf` | Figure 3: cost per bit by degree; made by `generator/make_figures.py` from `data/census.json`. |

Figure 1 (comb sums) is drawn with TikZ inside `artigo2.tex`.

**Compile** (TeX Live or MacTeX with `biblatex`):

```bash
cd paper
pdflatex artigo2 && bibtex artigo2 && pdflatex artigo2 && pdflatex artigo2
```

or `make paper` from the repository root.

**Numbering.** Theorems, propositions, lemmas, corollaries, definitions, examples and
observations share one counter. `docs/CLAIMS.md` uses the numbers of the compiled PDF:
Def. 1, Prop. 2, Lemma 3, Def. 4, Thm. 5, Thm. 6, Prop. 7, Cor. 8, Ex. 9, Cor. 10,
Prop. 11, Obs. 12. If the text changes and the numbering moves, update `CLAIMS.md`.
