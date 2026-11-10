#!/bin/sh
# Regenerates data/greedy_beyond150.txt (greedy count, lexicographic ties, for all members
# with 151 <= m <= 300 and m in {500, 800, 1100}; about 4 minutes) and checks it.
set -e
cd "$(dirname "$0")"
gcc -O2 -o greedy greedy.c
{ echo "# m b c dXOR CX(lexicographic) bestRandom(-1: not run) 3m-c-3 ; greedy fam2, all members with 151<=m<=300 and m in {500,800,1100}"
  ./greedy fam2 151 300 0
  for m in 500 800 1100; do ./greedy fam2 $m $m 0; done; } > greedy_beyond150.txt
cmp greedy_beyond150.txt ../data/greedy_beyond150.txt && echo "identical to data/greedy_beyond150.txt"
python3 analyze_greedy_beyond150.py greedy_beyond150.txt
