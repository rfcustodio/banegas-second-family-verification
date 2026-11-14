#!/usr/bin/env python3
"""Compare concrete heuristic special-strip SLPs with F2 Algorithm 1/2 SLPs.

Never substitute SAT-optimal gate count for heuristic measured depth.
The augmented Pareto front is among the explicitly generated SLPs only.
"""
import csv
import json
from collections import defaultdict
from pathlib import Path
OUT=Path(__file__).resolve().parent/"results"

def load(name):
    with (OUT/name).open(newline="") as f:return list(csv.DictReader(f))

def dominates(a,b):
    return (a["gates"]<=b["gates"] and a["depth"]<=b["depth"]
            and (a["gates"]<b["gates"] or a["depth"]<b["depth"]))

def main():
    allslps=load("all_f2_slps.csv")
    special=load("special_heuristic_slps.csv")
    by=defaultdict(list)
    for r in allslps:
        by[int(r["m"])].append(dict(m=int(r["m"]),b=int(r["b"]),c=int(r["c"]),
                                 method=r["method"],gates=int(r["gates"]),depth=int(r["depth"])))
    for r in special:
        assert r["verified"]=="True"
        by[int(r["m"])].append(dict(m=int(r["m"]),b=int(r["b"]),c=int(r["c"]),
                                 method="F2 heuristic strips",gates=int(r["heuristic_gates"]),
                                 depth=int(r["heuristic_depth"])))
    frontier=[];effects=[]
    for m,rs in sorted(by.items()):
        f=[r for r in rs if not any(dominates(s,r) for s in rs)]
        uniq={}
        for r in sorted(f,key=lambda x:(x["gates"],x["depth"],x["b"],x["c"],x["method"])):
            uniq.setdefault((r["gates"],r["depth"]),r)
        frontier.extend(uniq.values())
        if any(r["method"]=="F2 heuristic strips" for r in rs):
            old=[r for r in rs if r["method"]!="F2 heuristic strips"]
            new=[r for r in rs if r["method"]=="F2 heuristic strips"][0]
            old_area=min(r["gates"] for r in old)
            old_depth=min(r["depth"] for r in old)
            effects.append(dict(m=m,strip_gates=new["gates"],strip_depth=new["depth"],
                                old_min_gates=old_area,old_min_depth=old_depth,
                                new_min_gates=min(r["gates"] for r in rs),
                                new_min_depth=min(r["depth"] for r in rs),
                                strip_on_frontier=any(r["method"]=="F2 heuristic strips" for r in uniq.values())))
    def write(name,rows):
        with (OUT/name).open("w",newline="") as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    write("pareto_f2_with_heuristic_strips.csv",frontier)
    write("special_frontier_effect.csv",effects)
    meta={"special_members":len(effects),
          "special_on_frontier":sum(r["strip_on_frontier"] for r in effects),
          "special_improve_area":sum(r["new_min_gates"]<r["old_min_gates"] for r in effects),
          "special_improve_depth":sum(r["new_min_depth"]<r["old_min_depth"] for r in effects),
          "scope":"Generated SLPs only; SAT area optima not paired with heuristic depth"}
    assert len(effects)==15
    (OUT/"special_frontier_effect.json").write_text(json.dumps(meta,indent=2)+"\n")
    print(json.dumps(meta))
if __name__=="__main__":main()
