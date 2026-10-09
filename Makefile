# Shortcuts for the co-authors. Run from the repository root.
PY ?= python3

.PHONY: check check-full figures paper data clean

check:            ## fast checks of every statement (about 15 s)
	./run_quick_checks.sh

check-full:       ## the same checks over the full range of the paper (m <= 300, about 3 min)
	$(PY) checks/verify_statements.py --mmax 300
	$(PY) checks/reproduce_tables.py
	$(PY) checks/analyze_paar150.py
	$(PY) checks/compare_censuses.py
	$(PY) generator/lowdepth.py --all 260

figures:          ## regenerate Figures 2 and 3 (needs numpy and matplotlib)
	$(PY) generator/make_figures.py

paper:            ## compile paper/artigo2.pdf (needs LaTeX with biblatex)
	cd paper && pdflatex -interaction=nonstopmode artigo2 && bibtex artigo2 && \
	pdflatex -interaction=nonstopmode artigo2 && pdflatex -interaction=nonstopmode artigo2

data:             ## regenerate data/ from scratch (needs a C compiler; about 20 min)
	gcc -O2 -o xorred generator/xorred.c
	$(PY) -c "exec('for m in range(5,151):\n for c in range(1,m):\n  b=m-2*c\n  if b>c: print(m,b+c,b,c)')" > pairs150.txt
	./xorred list 20 5 < pairs150.txt > data/paar150.txt
	./xorred fam2 5 1100 > data/fam2_irr.txt
	./xorred fam1 5 1100 > data/fam1_irr.txt
	./xorred tri 2 1100 > data/tri.txt
	rm -f pairs150.txt
	@echo "Note: the original data/paar150.txt used seeds 5 and 6 on two halves; only the RG columns may differ."

clean:            ## remove LaTeX and build by-products
	cd paper && rm -f *.aux *.bbl *.blg *.log *.out *.run.xml *-blx.bib *.bcf
	rm -f xorred
