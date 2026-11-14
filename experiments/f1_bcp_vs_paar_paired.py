#!/usr/bin/env python3
"""Paired, per-polynomial comparison of BCP Eq14 and Conta-XOR/Paar.

Matches the same irreducible polynomial (m,b,c), not merely the degree.
The special BCP Algorithm 3 (b=2c) is excluded from the paired sample.
"""
import csv
import json
from pathlib import Path
from statistics import mean, median
OUT=Path(__file__).resolve().parent/"results"

def load(name):
    with (OUT/name).open(newline="") as f:return list(csv.DictReader(f))

def main():
    bcp=load("f1_bcp_measured.csv")
    paar=load("f1_contaxor_baseline.csv")
    baseline={(int(r["m"]),int(r["b"]),int(r["c"])):r for r in paar}
    assert len(baseline)==len(paar), "Repeated heuristic polynomial"
    keys=set()
    paired=[]
    for r in bcp:
        key=tuple(int(r[k]) for k in ("m","b","c"))
        assert key not in keys, "Repeated BCP polynomial"
        keys.add(key)
        if key not in baseline:continue
        h=baseline[key]
        a,d=int(r["gates"]),int(r["depth"])
        ha,hd=int(h["gates"]),int(h["depth"])
        paired.append(dict(m=key[0],b=key[1],c=key[2],
            bcp_gates=a,bcp_depth=d,heuristic_gates=ha,heuristic_depth=hd,
            heuristic_minus_bcp_gates=ha-a,heuristic_minus_bcp_depth=hd-d,
            bcp_dominates_heuristic=(a<=ha and d<=hd and (a<ha or d<hd)),
            heuristic_dominates_bcp=(ha<=a and hd<=d and (ha<a or hd<d))))
    assert paired,"No matching BCP and heuristic polynomials"
    assert len({(r["m"],r["b"],r["c"]) for r in paired})==len(paired)
    with (OUT/"f1_bcp_vs_paar_paired.csv").open("w",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=list(paired[0]))
        writer.writeheader();writer.writerows(paired)
    differences=[r["heuristic_minus_bcp_gates"] for r in paired]
    depth_differences=[r["heuristic_minus_bcp_depth"] for r in paired]
    summary=dict(
        comparison="Same irreducible F1 polynomial, BCP Eq14 vs Conta-XOR/Paar",
        pairs=len(paired),distinct_degrees=len({r["m"] for r in paired}),
        bcp_smaller_area=sum(x>0 for x in differences),
        heuristic_smaller_area=sum(x<0 for x in differences),
        equal_area=sum(x==0 for x in differences),
        bcp_smaller_depth=sum(x>0 for x in depth_differences),
        heuristic_smaller_depth=sum(x<0 for x in depth_differences),
        equal_depth=sum(x==0 for x in depth_differences),
        bcp_pareto_dominates=sum(r["bcp_dominates_heuristic"] for r in paired),
        heuristic_pareto_dominates=sum(r["heuristic_dominates_bcp"] for r in paired),
        mean_heuristic_minus_bcp_gates=round(mean(differences),6),
        median_heuristic_minus_bcp_gates=median(differences),
        excluded_special_case="b=2c: optimized BCP Algorithm 3 not implemented")
    (OUT/"f1_bcp_vs_paar_paired.json").write_text(json.dumps(summary,indent=2)+"\n")
    print(json.dumps(summary,indent=2))

if __name__=="__main__":main()
