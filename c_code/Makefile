# Software measurement of the word-level reductions (Corollary 16 of the
# paper, for the second family, and its specialisation with C = H for the
# first family), against the NIST pentanomials and the irreducible trinomials.
#
# The reported numbers come from the two scalar builds, bench-clang and
# bench-gcc. Auto-vectorization is off on purpose: with it, clang (in some
# kernels) and gcc (in most of them) read with wide loads what was just
# written with narrow stores, and the blocked store-to-load forwards change
# the ranking of the kernels. The -vec builds keep the vectorizer on to show
# that effect; `make results` records it in the raw/op column.
#
#   make test       correctness of every kernel against a bitwise reference
#   make results    results-<build>.txt (summary) and samples-<build>.csv
#                   (every sample) for the four builds
#   make layouts    the scalar builds again with LAYOUTS different function
#                   placements; layouts.txt gives, for each routine, the
#                   minimum and the median over the trials in every placement
#                   and their spread over the placements. The paper reports
#                   the median over the placements of the minimum over the
#                   trials (column "median" of the "min" blocks).
#   make summary    the minima of the four builds side by side
#   make paper      the body of Table 12 and every number quoted in
#                   Section IX-G, from the layout runs and the -vec builds
#   make recurrence-571-22  optional high-to-low comb variant of f_(527,22):
#                   eight shuffled placements, summaries and raw samples
CLANG  ?= clang
GCC    ?= gcc
BASE    = -O3 -march=native -mpclmul -Wall -Wextra -fomit-frame-pointer
CLANG_SCALAR = -fno-vectorize -fno-slp-vectorize
GCC_SCALAR   = -fno-tree-vectorize

CPU    ?= 2
ITERS  ?= 200000
TRIALS ?= 21
# Raw PMU event counted next to cycles and instructions. 0x8203 is
# ld_blocks.store_forward (event 0x03, umask 0x82) on Intel Golden Cove and
# Raptor Cove P-cores; look up the code for other cores with
# `perf list --details ld_blocks.store_forward`.
RAW    ?= 0x8203
# Function placement for `make layouts`: each layout links the program with
# its sections shuffled by the linker (mold: --shuffle-sections=SEED).
LAYOUTS ?= 1 2 3 4 5 6 7 8
SHUFFLE  = -ffunction-sections -fuse-ld=mold -Wl,--shuffle-sections=

BINS = bench-clang bench-gcc bench-clang-vec bench-gcc-vec
RUN  = --cpu $(CPU) --iters $(ITERS) --trials $(TRIALS) --raw $(RAW)

all: $(BINS) t_clmul
bench-clang: bench.c gf2m.h
	$(CLANG) $(BASE) $(CLANG_SCALAR) -DBUILD_FLAGS='"$(BASE) $(CLANG_SCALAR)"' -o $@ bench.c
bench-gcc: bench.c gf2m.h
	$(GCC) $(BASE) $(GCC_SCALAR) -DBUILD_FLAGS='"$(BASE) $(GCC_SCALAR)"' -o $@ bench.c
bench-clang-vec: bench.c gf2m.h
	$(CLANG) $(BASE) -DBUILD_FLAGS='"$(BASE)"' -o $@ bench.c
bench-gcc-vec: bench.c gf2m.h
	$(GCC) $(BASE) -DBUILD_FLAGS='"$(BASE)"' -o $@ bench.c
t_clmul: t_clmul.c
	$(CC) -O2 -mpclmul -o $@ t_clmul.c

test: $(BINS) t_clmul
	./t_clmul
	for b in $(BINS); do ./$$b --test --tests 200 || exit 1; done
run: bench-clang bench-gcc
	./bench-clang $(RUN)
	./bench-gcc   $(RUN)
results-%.txt: bench-%
	./$< $(RUN) --csv samples-$*.csv > $@
results: $(BINS:bench-%=results-%.txt)
summary: results
	python3 summarize.py results-clang.txt results-gcc.txt results-clang-vec.txt results-gcc-vec.txt

layouts: bench.c gf2m.h
	mkdir -p layout
	for s in $(LAYOUTS); do \
	  $(CLANG) $(BASE) $(CLANG_SCALAR) $(SHUFFLE)$$s -DBUILD_FLAGS='"$(BASE) $(CLANG_SCALAR) $(SHUFFLE)'$$s'"' \
	    -o layout/bench-clang-L$$s bench.c || exit 1; \
	  $(GCC) $(BASE) $(GCC_SCALAR) $(SHUFFLE)$$s -DBUILD_FLAGS='"$(BASE) $(GCC_SCALAR) $(SHUFFLE)'$$s'"' \
	    -o layout/bench-gcc-L$$s bench.c || exit 1; \
	  ./layout/bench-clang-L$$s $(RUN) --seed $$s --csv layout/samples-clang-L$$s.csv \
	    > layout/results-clang-L$$s.txt || exit 1; \
	  ./layout/bench-gcc-L$$s   $(RUN) --seed $$s --csv layout/samples-gcc-L$$s.csv \
	    > layout/results-gcc-L$$s.txt   || exit 1; \
	done
	$(MAKE) --no-print-directory layouts.txt
layouts.txt: $(wildcard layout/results-*-L*.txt)
	{ for c in clang gcc; do for s in min median; do \
	    echo "# $$c, $(words $(LAYOUTS)) function placements"; \
	    python3 summarize.py --spread --stat $$s layout/results-$$c-L*.txt; echo; \
	  done; done; } > layouts.txt
	cat layouts.txt

recurrence-571-22: bench.c gf2m.h
	mkdir -p layout/recurrence-571-22
	for s in $(LAYOUTS); do \
	  $(CLANG) $(BASE) $(CLANG_SCALAR) $(SHUFFLE)$$s -DGF2M_DESCENDING_COMB_571_22=1 \
	    -DBUILD_FLAGS='"$(BASE) $(CLANG_SCALAR) -DGF2M_DESCENDING_COMB_571_22=1"' \
	    -o layout/recurrence-571-22/bench-clang-L$$s bench.c || exit 1; \
	  $(GCC) $(BASE) $(GCC_SCALAR) $(SHUFFLE)$$s -DGF2M_DESCENDING_COMB_571_22=1 \
	    -DBUILD_FLAGS='"$(BASE) $(GCC_SCALAR) -DGF2M_DESCENDING_COMB_571_22=1"' \
	    -o layout/recurrence-571-22/bench-gcc-L$$s bench.c || exit 1; \
	  ./layout/recurrence-571-22/bench-clang-L$$s $(RUN) --seed $$s \
	    --filter 'second(527,22)' --csv layout/recurrence-571-22/samples-clang-L$$s.csv \
	    > layout/recurrence-571-22/results-clang-L$$s.txt || exit 1; \
	  ./layout/recurrence-571-22/bench-gcc-L$$s $(RUN) --seed $$s \
	    --filter 'second(527,22)' --csv layout/recurrence-571-22/samples-gcc-L$$s.csv \
	    > layout/recurrence-571-22/results-gcc-L$$s.txt || exit 1; \
	done
	python3 summarize.py --recurrence > layout/recurrence-571-22/summary.txt
	cat layout/recurrence-571-22/summary.txt

paper:
	python3 summarize.py --paper > paper_numbers.txt
	cat paper_numbers.txt

vectors: bench-clang
	./bench-clang --test --vectors --tests 5 > vectors.txt
clean:
	rm -f $(BINS) bench t_clmul
	rm -rf layout
.PHONY: all test run results summary layouts recurrence-571-22 paper vectors clean
