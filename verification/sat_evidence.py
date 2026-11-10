#!/usr/bin/env python3
"""Evidence for the SAT results of Tables 2 and 5.

For every instance:
  * checks that every row of R' is nonzero (hypothesis of Lemma 19, so that
    Red = (number of low inputs) + Red(R'));
  * K = claimed value: solves the CNF, decodes the program, adds one gate per low
    input, and checks the complete program symbolically against the reduction
    matrix; the program is written to data/sat/programs.json;
  * K - 1 (only where the paper claims optimality): writes the CNF in DIMACS form,
    runs the standalone CaDiCaL with a DRAT proof and checks the proof with
    drat-trim. CNF and proof are stored compressed in data/sat/.
All sizes, hashes, times and tool versions go to data/sat/evidence.json.

Usage: python3 sat_evidence.py CADICAL DRAT_TRIM [OUTDIR]
"""
import gzip, hashlib, json, lzma, os, subprocess, sys, tempfile, time
import pysat
from pysat.solvers import Cadical153
exec(open('slp_sat.py').read().split("if __name__ == '__main__':")[0])
exec(open('exact_base.py').read().split('if __name__ == "__main__":')[0])

CADICAL, DRAT = sys.argv[1], sys.argv[2]
OUT = sys.argv[3] if len(sys.argv) > 3 else '../data/sat'
os.makedirs(OUT, exist_ok=True)

def full_rows(N, k, ex):
    """reduction matrix of x^k + sum x^e over N input coefficients (row i = output i)."""
    col = [0] * k; col[0] = 1; rows = [0] * k
    for j in range(N):
        if j > 0:
            top = col[k - 1]; col = [0] + col[:-1]
            if top:
                for e in ex: col[e] ^= 1
        for i in range(k):
            if col[i]: rows[i] |= 1 << j
    return rows

# (name, table, rows of R', number of high inputs, number of low inputs k,
#  input count N, exponents, claimed gates, optimality claimed?)
inst = []
for (m, b, c, K, opt) in [(4,2,1,6,1),(5,3,1,10,1),(6,4,1,14,1),(7,5,1,16,1),(7,3,2,16,1),
                          (8,6,1,19,1),(9,5,2,21,1),(9,7,1,22,0),(10,8,1,24,0),
                          (11,7,2,27,0),(11,9,1,27,0)]:
    rows, n = reduced_targets(m, b, c)
    inst.append((f"f_{b}_{c}", "Table 5" + (" and Table 2 (R2)" if m <= 7 else ""),
                 rows, n, m, 2 * m - 1, [b + c, b, c, 0], K, bool(opt)))
for (bp, cp, R1) in [(2,1,7),(3,1,12),(4,1,15),(5,1,18),(3,2,18)]:
    k = bp + 2 * cp
    rows, n, _ = strip_reduced(bp, cp, 2 * k - 1)
    inst.append((f"R1_f_{bp}_{cp}", "Table 2 (R1)", rows, n, k, 2 * k, [bp + cp, bp, cp, 0], R1, True))

def sha(path):
    return hashlib.sha256(open(path, 'rb').read()).hexdigest()

def dimacs(cl, path):
    nv = max(abs(l) for c in cl for l in c)
    with open(path, 'w') as f:
        f.write(f"p cnf {nv} {len(cl)}\n")
        for c in cl: f.write(' '.join(map(str, c)) + ' 0\n')
    return nv

ver = subprocess.run([CADICAL, '--version'], capture_output=True, text=True).stdout.strip()
evidence = {"tools": {"pysat": pysat.__version__, "pysat solver": "Cadical153 (CaDiCaL 1.5.3)",
                      "standalone CaDiCaL": ver, "drat-trim": "github.com/marijnheule/drat-trim"},
            "encoding": "verification/slp_sat.py, function encode", "instances": []}
programs = {}
ok_all = True
for (name, table, rows, n, k, N, ex, K, opt) in inst:
    assert all(rows), f"{name}: a row of R' is zero"
    Kr = K - k                               # gates for R'
    T = sorted({t for t in rows if bin(t).count('1') >= 2})
    rec = {"name": name, "table": table, "low inputs": k, "high inputs": n,
           "distinct targets": len(T), "claimed gates": K, "optimality claimed": opt}
    # --- K: program
    cl, pool, _ = encode(rows, n, Kr)
    t0 = time.time()
    with Cadical153(bootstrap_with=cl) as s:
        assert s.solve(), name
        prog = decode(s.get_model(), pool, n, Kr)
    rec["solve K (s)"] = round(time.time() - t0, 1)
    # complete program over all N inputs: low input i is input i, high input t is k+t
    sig = [1 << (k + t) for t in range(n)]
    gates = []
    name_of = [f"d{k+t}" for t in range(n)]
    for i, (p, q) in enumerate(prog):
        sig.append(sig[p] ^ sig[q]); gates.append(f"t{i} = {name_of[p]} ^ {name_of[q]}")
        name_of.append(f"t{i}")
    where = {}
    for idx, v in enumerate(sig): where.setdefault(v, idx)
    outs = []
    for i, r in enumerate(rows):
        v = 0
        for t in range(n):
            if r >> t & 1: v |= 1 << (k + t)
        idx = where[v]                       # KeyError means the program is wrong
        outs.append(f"r{i} = d{i} ^ {name_of[idx]}")
    total = len(gates) + len(outs)
    target = full_rows(N, k, ex)
    computed = [(1 << i) | (sig[where[sum(1 << (k + t) for t in range(n) if rows[i] >> t & 1)]]) for i in range(k)]
    good = computed == target and total == K
    rec["program check"] = "PASS" if good else "FAIL"
    ok_all &= good
    programs[name] = {"inputs": f"d0..d{N-1} (coefficients of the dividend)", "gates": gates,
                      "outputs": outs, "total XOR gates": total}
    # --- K-1: DRAT certificate
    if opt:
        cl, pool, _ = encode(rows, n, Kr - 1)
        with tempfile.TemporaryDirectory() as tmp:
            cnf = os.path.join(tmp, 'f.cnf'); prf = os.path.join(tmp, 'f.drat')
            nv = dimacs(cl, cnf)
            t0 = time.time()
            r = subprocess.run([CADICAL, '-q', '--no-binary', cnf, prf], capture_output=True, text=True)
            ts = time.time() - t0
            t0 = time.time()
            d = subprocess.run([DRAT, cnf, prf, '-t', '20000'], capture_output=True, text=True)
            td = time.time() - t0
            verified = r.returncode == 20 and 's VERIFIED' in d.stdout
            ok_all &= verified
            base = os.path.join(OUT, f"{name}_K{K-1}")
            with open(cnf, 'rb') as f, gzip.open(base + '.cnf.gz', 'wb', 9) as g: g.write(f.read())
            with open(prf, 'rb') as f, lzma.open(base + '.drat.xz', 'wb', preset=9) as g: g.write(f.read())
            rec["UNSAT at"] = K - 1
            rec["cnf"] = {"file": os.path.basename(base) + '.cnf.gz', "variables": nv, "clauses": len(cl),
                          "sha256 (uncompressed)": sha(cnf)}
            rec["proof"] = {"file": os.path.basename(base) + '.drat.xz',
                            "bytes (uncompressed)": os.path.getsize(prf), "sha256 (uncompressed)": sha(prf)}
            rec["cadical (s)"] = round(ts, 1); rec["drat-trim (s)"] = round(td, 1)
            rec["drat-trim"] = "s VERIFIED" if verified else "FAILED"
    evidence["instances"].append(rec)
    print(f"{name:12s} {table:28s} K={K:3d} program {rec['program check']}"
          + (f"  K-1={K-1:3d} UNSAT, DRAT {rec['drat-trim']} ({rec['proof']['bytes (uncompressed)']} bytes)" if opt else "  (best found, optimality not claimed)"),
          flush=True)
json.dump(programs, open(os.path.join(OUT, 'programs.json'), 'w'), indent=1)
json.dump(evidence, open(os.path.join(OUT, 'evidence.json'), 'w'), indent=1)
print("ALL SAT EVIDENCE VERIFIED" if ok_all else "FAILURE")
sys.exit(0 if ok_all else 1)
