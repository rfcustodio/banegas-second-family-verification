#!/usr/bin/env python3
"""Reproducible cross-family Pareto audit, exact counts and effect sizes.

Compares measured F1 Conta-XOR/Paar circuits against measured F2 circuits.
This does NOT estimate the depth of the original BCP construction.
"""
import csv
import json
from pathlib import Path
from statistics import mean,median
OUT=Path(__file__).resolve().parent/"results"
def load(name):
    with (OUT/name).open(newline="") as f:return list(csv.DictReader(f))
def main():
    s=load("cross_family_measured_summary.csv")
    f1=load("f1_contaxor_baseline.csv")
    pareto=load("cross_family_measured_pareto.csv")
    assert len(s)==len({int(r["m"]) for r in s})
    assert len(f1)==138
    assert len(s)==75
    assert len({int(r["m"]) for r in pareto})==len(s)
    a=[int(r["f1_best_gates"])-int(r["f2_best_gates"]) for r in s]
    d=[int(r["f2_best_depth"])-int(r["f1_best_depth"]) for r in s]
    assert all(v>0 for v in a), "F2 must have lower gate count on every sampled degree"
    assert all(v>=0 for v in d), "F2 must not have lower minimum depth in this sample"
    assert sum(v>0 for v in d)==74 and sum(v==0 for v in d)==1
    for r in s:
        m=int(r["m"])
        q=[p for p in pareto if int(p["m"])==m]
        assert q
        assert (r["f1_contributes_to_joint_frontier"]=="True")==any(p["family"]=="F1" for p in q)
    savings=[100*v/int(r["f1_best_gates"]) for v,r in zip(a,s)]
    stats=dict(
        basis="Verified SLPs: F1 Conta-XOR/Paar heuristic vs F2 algorithms and heuristic strips; NOT BCP",
        degrees=len(s),f1_verified_circuits=len(f1),
        f2_lower_area=sum(v>0 for v in a),
        f1_lower_depth=sum(v>0 for v in d),
        equal_minimum_depth=sum(v==0 for v in d),
        f1_pareto_degrees=sum(r["f1_contributes_to_joint_frontier"]=="True" for r in s),
        f2_pareto_degrees=sum(r["f2_contributes_to_joint_frontier"]=="True" for r in s),
        mean_area_saving_percent=round(mean(savings),6),
        median_area_saving_percent=round(median(savings),6),
        min_area_saving_percent=round(min(savings),6),
        max_area_saving_percent=round(max(savings),6),
        depth_tie_degrees=[int(r["m"]) for r,v in zip(s,d) if v==0],
        unpaired_f1_degrees=20,
    )
    (OUT/"cross_family_statistics.json").write_text(json.dumps(stats,indent=2)+"\n")
    print(json.dumps(stats,indent=2))
if __name__=="__main__":main()
