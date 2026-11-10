SHELL := /bin/bash
# Shortcuts for the co-authors. Run from the repository root.
PY ?= python3

.PHONY: check check-full verify-all sat-proofs greedy-beyond150 figures paper data clean

check:            ## fast checks of every statement (about 15 s)
	./run_quick_checks.sh

check-full:       ## the same checks over a larger range (m <= 300, about 3 min)
	$(PY) checks/verify_statements.py --mmax 300
	$(PY) checks/verify_chain.py --mmax 300
	$(PY) checks/reproduce_tables.py
	$(PY) checks/analyze_paar150.py
	$(PY) checks/compare_censuses.py
	$(PY) generator/lowdepth.py --all 260

verify-all:       ## complete verification up to m = 1100, as in the paper (gcc, python-sat; about 15 min)
	sh verification/run_all.sh > verification/output.txt
	diff <(grep -v '([0-9.]*s)' verification/output.txt) <(grep -v '([0-9.]*s)' verification/expected_output.txt) && echo "verification output matches expected_output.txt"

sat-proofs:       ## build CaDiCaL and drat-trim at the recorded commits, regenerate and check the 12 DRAT certificates (about 5 min)
	rm -rf build-sat && mkdir build-sat
	cd build-sat && git clone -q https://github.com/arminbiere/cadical.git && cd cadical && git checkout -q c607304 && ./configure > /dev/null && $(MAKE) -s > /dev/null
	cd build-sat && git clone -q https://github.com/marijnheule/drat-trim.git && cd drat-trim && git checkout -q 2e3b2dc && $(MAKE) -s > /dev/null
	CADICAL=$(CURDIR)/build-sat/cadical/build/cadical sh verification/check_sat_proofs.sh build-sat/none $(CURDIR)/build-sat/drat-trim/drat-trim

greedy-beyond150: ## regenerate data/greedy_beyond150.txt (greedy beyond m = 150; about 4 min) and check it
	sh verification/greedy_beyond150.sh

figures:          ## regenerate Figures 2 and 3 (needs matplotlib)
	$(PY) generator/make_figures.py

paper:            ## compile paper/main.pdf
	cd paper && pdflatex -interaction=nonstopmode main && bibtex main && \
	pdflatex -interaction=nonstopmode main && pdflatex -interaction=nonstopmode main

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
	rm -rf build-sat
	cd paper && rm -f *.aux *.blg *.log *.out *.run.xml *-blx.bib *.bcf
	rm -f xorred
	cd verification && rm -f alg1verify alg2verify census greedy sec.txt fst.txt tri.txt g150.txt output.txt census_verified.json greedy_beyond150.txt t1.txt t2.txt esp.txt pmin.txt other_families.json multiplier.json
