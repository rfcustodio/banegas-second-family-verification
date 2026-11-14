#!/usr/bin/env python3
"""Independent area/depth experiment; does not overwrite published results.

Run from the repository root:
    python3 experiments/area_depth_1100.py

Depth is measured from the actual generated XOR straight-line program for
Algorithms 1 and 2. BCP and SAT-optimal special strip depths are deliberately
left blank: gate counts alone cannot determine their depth.
"""
import csv
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "generator"))
sys.path.insert(0, str(ROOT / "algorithm2"))
from fam2 import program as alg1_program
from alg2prog import program as alg2_program

OUT = ROOT / "experiments" / "results"
BASE = {(2, 1): (6, 7), (3, 1): (10, 12),
        (4, 1): (14, 15), (5, 1): (16, 18),
        (3, 2): (16, 18)}

def load_pairs(name):
    return [tuple(map(int, line.split())) for line in
            (ROOT / "data" / name).read_text().splitlines()
            if line.strip() and not line.startswith("#")]

def n_chain(b, c):
    return c * ((b + c) // (3 * c)) + max(0, (b + c) % (3 * c) - 2 * c)

def special_cost(b, c):
    g = math.gcd(b, c)
    base = (b // g, c // g)
    if base not in BASE:
        return None
    r2, r1 = BASE[base]
    return (g - 1) * r1 + r2

def candidates():
    for m, b, c in load_pairs("fam2_irr.txt"):
        yield m, "F2 closed form", b, c, 3*m-c-3
        yield m, "F2 chain", b, c, 3*m-3-n_chain(b,c)
        s = special_cost(b,c)
        if s is not None:
            yield m, "F2 special strips", b, c, s
    for m, b, c in load_pairs("fam1_irr.txt"):
        yield m, "F1 BCP", b, c, (12*m//5-1 if b==2*c else 3*m-2)

def depth(method,b,c):
    m = b+2*c
    if method == "F2 closed form":
        p, outputs = alg1_program(b,c)
        return len(p.gates), max(p.depth[o] for o in outputs)
    if method == "F2 chain":
        p, values, depths, _ = alg2_program(b,c)
        return len(p), max(depths[("r",i)] for i in range(m))
    return None, None

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    # Choose minimum XOR count independently for each method and degree.
    best={}
    for m,method,b,c,cost in candidates():
        if not 5 <= m <= 1100: continue
        key=(m,method)
        if key not in best or (cost,b,c)<(best[key][0],best[key][1],best[key][2]):
            best[key]=(cost,b,c)
    rows=[]
    for (m,method),(cost,b,c) in sorted(best.items()):
        generated, d = depth(method,b,c)
        # The generator deduplicates coincident linear forms. For special
        # parameter ratios this can yield fewer gates than the stated bound.
        # Preserve both numbers rather than claiming that they must agree.
        if generated is not None and generated > cost:
            raise AssertionError(("SLP exceeds formula",m,method,b,c,generated,cost))
        rows.append(dict(m=m,method=method,b=b,c=c,xors=cost,
                         xors_per_bit=round(cost/m,9),
                         generated_xors="" if generated is None else generated,
                         gate_saving="" if generated is None else cost-generated,
                         depth="" if d is None else d,
                         depth_status=("measured from generated SLP" if d is not None
                                       else "not available; requires matching SLP")))
    fields=["m","method","b","c","xors","xors_per_bit","generated_xors","gate_saving","depth","depth_status"]
    with (OUT/"best_by_method.csv").open("w",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=fields)
        writer.writeheader();writer.writerows(rows)
    (OUT/"metadata.json").write_text(json.dumps({
        "range":[5,1100],"selection":"minimum XOR per method per degree",
        "depth":"actual SLP depth for F2 algorithms 1 and 2 only",
        "xors":"published construction formula or special SAT strip cost",
        "generated_xors":"actual SLP gate count; may be smaller because duplicate linear forms are shared",
        "missing":"F1 BCP and SAT-optimal special strip SLP depth",
        "note":"minimum-depth polynomials may differ from minimum-XOR polynomials"
    },indent=2)+"\n")
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("CSV generated; install matplotlib to produce plots")
        return
    methods=["F1 BCP","F2 closed form","F2 chain","F2 special strips"]
    fig,ax=plt.subplots(figsize=(10,4.8))
    for method in methods:
        r=[v for v in rows if v["method"]==method]
        ax.scatter([v["m"] for v in r],[v["xors_per_bit"] for v in r],
                   s=8,alpha=.7,label=method)
    ax.set(xlabel="Degree m",ylabel="XOR gates per output bit",xlim=(0,1100))
    ax.legend(fontsize=8);fig.tight_layout()
    fig.savefig(OUT/"xor_per_bit.pdf");plt.close(fig)
    fig,ax=plt.subplots(figsize=(10,4.8))
    for method in methods:
        r=[v for v in rows if v["method"]==method and v["depth"]!=""]
        if r:
            ax.scatter([v["m"] for v in r],[v["depth"] for v in r],
                       s=8,alpha=.7,label=method)
    ax.set(xlabel="Degree m",ylabel="XOR depth (generated SLP)",xlim=(0,1100))
    ax.legend(fontsize=8)
    ax.text(.02,.97,"F1 BCP and special strips: depth not yet available",
            transform=ax.transAxes,va="top",fontsize=8)
    fig.tight_layout();fig.savefig(OUT/"xor_depth.pdf");plt.close(fig)
    print(f"Wrote {len(rows)} per-method best records to {OUT}")

if __name__=="__main__":
    main()
