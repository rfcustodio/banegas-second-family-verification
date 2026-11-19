# Software measurement of the word-level reduction (Corollary 16).
#
# The reported numbers come from the two scalar builds, bench-clang and
# bench-gcc. Auto-vectorization is off on purpose: with it, clang (in some
# kernels) and gcc (in all of them) read with wide loads what was just written
# with narrow stores, and the blocked store-to-load forwards change the ranking
# of the kernels. The -vec builds keep the vectorizer on to show that effect;
# `make results` records it in the red:raw and sqr:raw columns.
CLANG  ?= clang
GCC    ?= gcc
BASE    = -O3 -march=native -mpclmul -Wall -Wextra -fomit-frame-pointer
CLANG_SCALAR = -fno-vectorize -fno-slp-vectorize
GCC_SCALAR   = -fno-tree-vectorize

CPU    ?= 2
ITERS  ?= 200000
TRIALS ?= 9
# Raw PMU event counted next to cycles and instructions. 0x8203 is
# ld_blocks.store_forward (event 0x03, umask 0x82) on Intel Golden Cove and
# Raptor Cove P-cores; look up the code for other cores with
# `perf list --details ld_blocks.store_forward`.
RAW    ?= 0x8203

BINS = bench-clang bench-gcc bench-clang-vec bench-gcc-vec

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
	./bench-clang --cpu $(CPU) --iters $(ITERS) --trials $(TRIALS) --raw $(RAW)
	./bench-gcc   --cpu $(CPU) --iters $(ITERS) --trials $(TRIALS) --raw $(RAW)
results-%.txt: bench-%
	./$< --cpu $(CPU) --iters $(ITERS) --trials $(TRIALS) --raw $(RAW) > $@
results: $(BINS:bench-%=results-%.txt)
vectors: bench-clang
	./bench-clang --vectors --tests 5 > vectors.txt
clean:
	rm -f $(BINS) bench t_clmul vectors.txt
.PHONY: all test run results vectors clean
