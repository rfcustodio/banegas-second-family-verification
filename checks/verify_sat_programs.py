#!/usr/bin/env python3
"""Checks the optimal (and best-found) programs of Tables 2 and 5 stored in
data/sat/programs.json, and the CNF files listed in data/sat/evidence.json.

* every program is evaluated symbolically (one bitmask per input coefficient) and
  compared with the reduction matrix of f_{b,c} over its 2m-1 inputs, or, for the
  R1 strip programs of Table 2, of the base polynomial G over 2*kappa inputs;
* its number of XOR gates must equal the value in the paper;
* each stored CNF (gzip) must have the SHA-256 recorded in evidence.json.
Standard library only. The DRAT proofs themselves are checked by
verification/check_sat_proofs.sh (they are distributed as a release asset).
"""
import gzip, hashlib, json, os, re, sys
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'sat')
progs = json.load(open(os.path.join(D, 'programs.json')))
ev = json.load(open(os.path.join(D, 'evidence.json')))

def matrix(k, ex, N):
    col = [0] * k; col[0] = 1; rows = [0] * k
    for j in range(N):
        if j > 0:
            top = col[k - 1]; col = [0] + col[:-1]
            if top:
                for e in ex: col[e] ^= 1
        for i in range(k):
            if col[i]: rows[i] |= 1 << j
    return rows

# values stated in Tables 2 and 5
paper = {'f_2_1': 6, 'f_3_1': 10, 'f_4_1': 14, 'f_5_1': 16, 'f_3_2': 16, 'f_6_1': 19,
         'f_5_2': 21, 'f_7_1': 22, 'f_8_1': 24, 'f_7_2': 27, 'f_9_1': 27,
         'R1_f_2_1': 7, 'R1_f_3_1': 12, 'R1_f_4_1': 15, 'R1_f_5_1': 18, 'R1_f_3_2': 18}
bad = 0
for name, p in progs.items():
    strip = name.startswith('R1_')
    b, c = map(int, name.split('_')[-2:])
    k = b + 2 * c; N = 2 * k if strip else 2 * k - 1
    val = {f"d{i}": 1 << i for i in range(N)}
    gates = 0
    for line in p['gates'] + p['outputs']:
        lhs, a, bb = re.fullmatch(r"(\w+) = (\w+) \^ (\w+)", line).groups()
        assert lhs not in val, line
        val[lhs] = val[a] ^ val[bb]; gates += 1
    got = [val[f"r{i}"] for i in range(k)]
    ok = got == matrix(k, [b + c, b, c, 0], N) and gates == paper[name] == p['total XOR gates']
    bad += not ok
    print(f"{name:10s} {gates:3d} XOR gates (paper {paper[name]:3d}): {'PASS' if ok else 'FAIL'}")
for r in ev['instances']:
    if 'cnf' in r:
        h = hashlib.sha256(gzip.open(os.path.join(D, r['cnf']['file'])).read()).hexdigest()
        ok = h == r['cnf']['sha256 (uncompressed)'] and r['drat-trim'] == 's VERIFIED'
        bad += not ok
        print(f"{r['cnf']['file']:24s} sha256 {'matches' if ok else 'MISMATCH'}; UNSAT at {r['UNSAT at']} gates, DRAT {r['drat-trim']}")
print("ALL SAT PROGRAMS AND CNF FILES OK" if not bad else f"{bad} FAILURES")
sys.exit(1 if bad else 0)
