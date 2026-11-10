#!/bin/sh
# Full verification of the paper's computational claims (about 10 minutes on 2 cores).
set -e
cd "$(dirname "$0")"
gcc -O2 -o alg1verify alg1verify.c
gcc -O2 -o census census.c
gcc -O2 -o greedy greedy.c
echo "== Algorithm 1, depth, low-depth variant, strips, word level, coincidences (m <= 1100)"
./alg1verify 4 1100 | grep -v "^INFO" | tail -3
./alg1verify 571 571 | grep INFO
echo "== Irreducibility census (5 <= m <= 1100)"
./census sec 5 1100 > sec.txt
./census fst 5 1100 > fst.txt
./census tri 2 1100 > tri.txt
python3 analyze_census.py
echo "== Greedy (Conta-XOR) for m <= 150, 20 randomized runs"
./greedy fam2 5 150 20 > g150.txt
python3 analyze_greedy.py
echo "== Example 11 (Table 3), NIST-degree members (Tables 4 and 9): dXOR, Conta-XOR and depth"
for p in "16 11 6 5 0" "163 117 71 46 0" "233 158 83 75 0" "233 217 201 16 0" "409 294 179 115 0" \
         "409 337 265 72 0" "571 389 207 182 0" "571 465 359 106 0" "571 549 527 22 0" \
         "163 7 6 3 0" "283 12 7 5 0" "571 10 5 2 0" "233 74 0" "409 87 0"; do
  ./greedy one 0 $p
done
python3 depth_table3.py
echo "== Base polynomials: greedy strip programs, sweep over 4 <= kappa <= 40 (Section III; the optimal values of Table 2 are checked by SAT below)"
./greedy strip 200 40 | grep -c "" ; ./greedy strip 200 40 | grep SHORTER
python3 compose_strips.py 1100 200 | tail -1
echo "== Boyar and Peralta heuristic"
python3 boyar_peralta.py
echo "== Chain construction (Algorithm 2, Theorem 13) for m <= 1100, census with both constructions"
gcc -O2 -o alg2verify ../algorithm2/alg2verify.c
./alg2verify 4 1100 527 22
for p in "71 46" "83 75" "201 16" "179 115" "265 72" "207 182" "359 106" "527 22" "8 1" "6 1" "5 1"; do
  echo "$p $(python3 ../algorithm2/alg2prog.py $p)"
done
python3 ../algorithm2/census_alg2.py
echo "== Exact minima with SAT (Tables 2 and 5), composition of the optimal strip programs, heuristic column of Table 5"
python3 exact_small.py
python3 exact_base.py
python3 compose_sat.py
python3 heuristic_small.py
echo "== Other pentanomial families (Section IX-C, Table 7)"
./census t1 5 1100 > t1.txt
./census t2 5 1100 > t2.txt
./census esp 5 1100 > esp.txt
./census pmin 5 1100 > pmin.txt
python3 other_families.py
