#!/usr/bin/env python3
"""Enumerate every irreducible second-family member and both executable SLPs.

Outputs are separate from the published census and from best_by_method.csv.
Area is the *actual* number of gates in each generated SLP. Depth is the
longest input-to-output XOR path. No SAT optimality is claimed.
"""
import csv
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"generator"))
sys.path.insert(0,str(ROOT/"algorithm2"))
from fam2 import program as closed_form
from alg2prog import program as chain_form

OUT=ROOT/"experiments"/"results"
METHODS=("F2 closed form","F2 chain")

def dominates(a,b):
    return (a["gates"]<=b["gates"] and a["depth"]<=b["depth"] and
            (a["gates"]<b["gates"] or a["depth"]<b["depth"]))

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    members=[]
    for line in (ROOT/"data"/"fam2_irr.txt").read_text().splitlines():
        if not line.strip() or line.startswith("#"): continue
        m,b,c=map(int,line.split())
        if not 5<=m<=1100: continue
        p,outputs=closed_form(b,c)
        members.append(dict(m=m,b=b,c=c,method=METHODS[0],
                            gates=len(p.gates),depth=max(p.depth[o] for o in outputs)))
        gates,_,dep,_=chain_form(b,c)
        members.append(dict(m=m,b=b,c=c,method=METHODS[1],
                            gates=len(gates),depth=max(dep[("r",i)] for i in range(m))))
    assert len(members)==2*1508, f"Unexpected census: {len(members)}"
    groups={}
    for row in members: groups.setdefault(row["m"],[]).append(row)
    assert len(groups)==720
    pareto=[];summary=[]
    for m,rs in sorted(groups.items()):
        area=min(rs,key=lambda r:(r["gates"],r["depth"],r["b"],r["c"],r["method"]))
        dep=min(rs,key=lambda r:(r["depth"],r["gates"],r["b"],r["c"],r["method"]))
        frontier=[r for r in rs if not any(dominates(s,r) for s in rs)]
        # Remove duplicate (area,depth) points; retain deterministic representative.
        unique={}
        for r in sorted(frontier,key=lambda r:(r["gates"],r["depth"],r["b"],r["c"],r["method"])):
            unique.setdefault((r["gates"],r["depth"]),r)
        pareto.extend(unique.values())
        summary.append(dict(m=m,minimum_gates=area["gates"],area_b=area["b"],
                            area_c=area["c"],area_method=area["method"],
                            depth_at_minimum_area=area["depth"],
                            minimum_depth=dep["depth"],depth_b=dep["b"],
                            depth_c=dep["c"],depth_method=dep["method"],
                            gates_at_minimum_depth=dep["gates"],
                            pareto_points=len(unique)))
    def write(name,rows,cols):
        with (OUT/name).open("w",newline="") as f:
            w=csv.DictWriter(f,fieldnames=cols);w.writeheader();w.writerows(rows)
    write("all_f2_slps.csv",members,["m","b","c","method","gates","depth"])
    write("pareto_f2.csv",pareto,["m","b","c","method","gates","depth"])
    write("f2_area_depth_summary.csv",summary,list(summary[0]))
    # Check each computed frontier: no selected point is dominated, and
    # every generated SLP is dominated or has a matching Pareto point.
    by_degree={}
    for r in pareto: by_degree.setdefault(r["m"],[]).append(r)
    for m,rs in groups.items():
        front=by_degree[m]
        assert all(not any(dominates(q,p) for q in rs) for p in front)
        assert all(any((q["gates"]==p["gates"] and q["depth"]==p["depth"])
                       or dominates(q,p) for q in front) for p in rs)
    metadata={"degrees":len(groups),"irreducible_members":len(members)//2,
              "slps":len(members),"pareto_points":len(pareto),
              "degrees_with_tradeoff":sum(r["pareto_points"]>1 for r in summary),
              "methodology":"Measured generated XOR SLPs for both F2 constructions only",
              "exclusions":"F1 BCP and SAT-optimal special strips, pending executable SLPs"}
    (OUT/"pareto_metadata.json").write_text(json.dumps(metadata,indent=2)+"\n")
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print(json.dumps(metadata));return
    fig,ax=plt.subplots(figsize=(9,4.5))
    ax.scatter([r["m"] for r in summary],[r["depth_at_minimum_area"] for r in summary],
               s=8,label="Depth of minimum-area circuit",alpha=.6)
    ax.scatter([r["m"] for r in summary],[r["minimum_depth"] for r in summary],
               s=8,label="Minimum achievable depth (among generated SLPs)",alpha=.6)
    ax.set(xlabel="Degree m",ylabel="XOR depth",xlim=(0,1100))
    ax.legend(fontsize=8);fig.tight_layout()
    fig.savefig(OUT/"f2_depth_tradeoff.pdf");plt.close(fig)
    print(json.dumps(metadata))

if __name__=="__main__":
    main()
