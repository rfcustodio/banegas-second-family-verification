#!/usr/bin/env bash
# Runs every fast verification of the paper. Exit status is non-zero if any check fails.
set -u
cd "$(dirname "$0")"
status=0
run() { echo; echo "=================== $*"; "$@" || status=1; }
run python3 checks/verify_statements.py
run python3 checks/reproduce_tables.py
run python3 checks/analyze_paar150.py
run python3 checks/compare_censuses.py
run python3 generator/lowdepth.py --all 160
echo
if [ $status -eq 0 ]; then echo "ALL QUICK CHECKS PASSED"; else echo "SOME CHECKS FAILED"; fi
exit $status
