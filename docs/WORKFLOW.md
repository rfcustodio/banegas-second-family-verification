# How we work together on this repository

The repository is the common ground for checking and improving the paper. These rules
keep the paper and the evidence for it in step.

## Typical tasks

### Read and check the paper

1. Read `paper/artigo2.pdf`.
2. Run `./run_quick_checks.sh` (or `make check`). Every line should say `PASS`/`ok`.
3. For any statement you doubt, look it up in [CLAIMS.md](CLAIMS.md) and run the script
   listed there. Every script prints the value it computed next to the value printed in
   the paper.

### Report a problem

Open an **Issue** on GitHub with:

* the statement (for example "Observation 12 (d)" or "Table 2, row m = 233");
* the command you ran and its output;
* what you expected.

### Propose a change (text or code)

```bash
git checkout -b my-change          # work on a branch, never directly on main
# ... edit files ...
./run_quick_checks.sh              # all checks must pass
git commit -am "Short description of the change"
git push -u origin my-change
```

Then open a **Pull Request** on GitHub. The checks run automatically on the Pull
Request (tab *Actions*); a green mark means they passed.

### Change a number in the paper

Every number of the paper is guarded by a script. If you change one:

1. edit `paper/artigo2.tex`;
2. update the expected value in the script listed in [CLAIMS.md](CLAIMS.md)
   (the expected values are written next to the word `paper` in each script);
3. update the corresponding line of `CLAIMS.md`;
4. run `./run_quick_checks.sh`.

### Rebuild the paper

Requires a LaTeX installation with `biblatex` (TeX Live or MacTeX).

```bash
make paper        # = cd paper && pdflatex artigo2 && bibtex artigo2 && pdflatex artigo2 && pdflatex artigo2
```

### Regenerate the figures

Requires `numpy` and `matplotlib` (`pip install numpy matplotlib`).

```bash
make figures      # writes paper/fig_gain.pdf and paper/fig_census.pdf from data/
```

### Regenerate the raw data

Requires a C compiler. The census up to degree 1100 takes about 15 minutes; the greedy
counts up to degree 150 take a few minutes.

```bash
make data         # rebuilds everything in data/ (see data/README.md)
```

After regenerating, `git diff data/` should show no change; any difference is a finding
worth an Issue.

## Conventions

* The paper is written in English, without em dashes.
* Results that are new in the paper are marked with a blue diamond in the PDF; results
  from the literature are always cited.
* Scripts in `checks/` use only the Python standard library, so that anyone can run them
  without installing anything.
* Do not edit `independent/` to make it agree with `generator/`: the value of the
  independent suite comes from it being written separately. Discrepancies are reported
  as Issues and resolved by finding which side is wrong.
