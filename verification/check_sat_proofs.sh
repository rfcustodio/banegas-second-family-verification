#!/bin/sh
# Checks the DRAT certificates of the SAT optimality claims (Tables 2 and 5).
# Usage: verification/check_sat_proofs.sh PROOF_DIR [DRAT_TRIM]
#   PROOF_DIR: directory with the *.drat.xz files of the release asset
#              sat-proofs-v22.tar (https://github.com/rfcustodio/banegas-second-family-verification/releases)
#   DRAT_TRIM: path to drat-trim (default: drat-trim in PATH)
# If the environment variable CADICAL points to CaDiCaL 3.0.1 (commit c607304),
# a proof missing from PROOF_DIR is regenerated from the CNF instead; CaDiCaL is
# deterministic, so the regenerated proof has the hash recorded in evidence.json.
# The CNF files are in data/sat/; their hashes and the proof hashes are in
# data/sat/evidence.json. Needs python3, gzip, xz, sha256sum. About 2 minutes.
set -e
P=$1; DT=${2:-drat-trim}
cd "$(dirname "$0")/../data/sat"
T=$(mktemp -d); trap 'rm -rf "$T"' EXIT
status=0
python3 - <<'PY' > "$T/list"
import json
for r in json.load(open('evidence.json'))['instances']:
    if 'proof' in r:
        print(r['cnf']['file'], r['proof']['file'], r['cnf']['sha256 (uncompressed)'], r['proof']['sha256 (uncompressed)'])
PY
while read cnf prf hc hp; do
  gzip -dc "$cnf" > "$T/f.cnf"
  if [ -f "$P/$prf" ]; then xz -dc "$P/$prf" > "$T/f.drat"
  elif [ -n "$CADICAL" ]; then "$CADICAL" -q --no-binary "$T/f.cnf" "$T/f.drat" > /dev/null || true
  else echo "$prf not found and CADICAL not set"; status=1; continue; fi
  [ "$(sha256sum < "$T/f.cnf" | cut -d' ' -f1)" = "$hc" ] || { echo "$cnf: hash mismatch"; status=1; }
  [ "$(sha256sum < "$T/f.drat" | cut -d' ' -f1)" = "$hp" ] || { echo "$prf: hash mismatch"; status=1; }
  if "$DT" "$T/f.cnf" "$T/f.drat" -t 20000 | grep -q "s VERIFIED"; then
    echo "$cnf: UNSAT certified by $prf"
  else
    echo "$cnf: proof NOT verified"; status=1
  fi
done < "$T/list"
[ $status -eq 0 ] && echo "ALL DRAT CERTIFICATES VERIFIED" || echo "SOME CERTIFICATES FAILED"
exit $status
