#!/usr/bin/env python3
"""Cross-family Pareto analysis using measured, concrete circuits only.

F1 is the selected Conta-XOR/Paar baseline, NOT the BCP implementation.
F2 includes both algorithms and verified heuristic special strips.
No SAT area bound is assigned an unmeasured depth.
"""
import csv
import json
from collections import defaultdict
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT=Path(__file__).resolve().parent/"results"
def load(name):
    with (OUT/name).open(newline="") as f:return list(csv.DictReader(f))
def dominates(a,b):
    return (a["gates"]<=b["gates"] and a["depth"]<=b["depth"]
            and (a["gates"]<b["gates"] or a["depth"]<b["depth"]))
def main():
    rows=defaultdict(list)
    for r in load("all_f2_slps.csv"):
        m=int(r["m"])
        rows[m].append(dict(m=m,family="F2",method=r["method"],
            b=int(r["b"]),c=int(r["c"]),gates=int(r["gates"]),depth=int(r["depth"])))
    for r in load("special_heuristic_slps.csv"):
        assert r["verified"]=="True"
        m=int(r["m"])
        rows[m].append(dict(m=m,family="F2",method="F2 heuristic strips",
            b=int(r["b"]),c=int(r["c"]),gates=int(r["heuristic_gates"]),
            depth=int(r["heuristic_depth"])))
    f1=load("f1_contaxor_baseline.csv")
    for r in f1:
        m=int(r["m"])
        rows[m].append(dict(m=m,family="F1",method="F1 Conta-XOR/Paar heuristic",
            b=int(r["b"]),c=int(r["c"]),gates=int(r["gates"]),depth=int(r["depth"])))
    f1_degrees={int(r["m"]) for r in f1}
    f2_degrees={m for m,items in rows.items() if any(r["family"]=="F2" for r in items)}
    degrees=sorted(f1_degrees & f2_degrees)
    assert degrees, "No common degrees for measured cross-family circuits"
    summary=[];frontier=[]
    for m in degrees:
        candidates=rows[m]
        first=[r for r in candidates if r["family"]=="F1"]
        second=[r for r in candidates if r["family"]=="F2"]
        assert first and second
        best_f1=min(first,key=lambda r:(r["gates"],r["depth"]))
        best_f2=min(second,key=lambda r:(r["gates"],r["depth"]))
        min_f1_depth=min(r["depth"] for r in first)
        min_f2_depth=min(r["depth"] for r in second)
        nondominated=[r for r in candidates if not any(dominates(other,r) for other in candidates)]
        unique={}
        for r in sorted(nondominated,key=lambda r:(r["gates"],r["depth"],r["family"],r["method"])):
            unique.setdefault((r["gates"],r["depth"]),r)
        frontier.extend(unique.values())
        summary.append(dict(m=m,f1_best_gates=best_f1["gates"],
            f1_best_depth=min_f1_depth,f2_best_gates=best_f2["gates"],
            f2_best_depth=min_f2_depth,
            f2_area_saving_percent=round(100*(best_f1["gates"]-best_f2["gates"])/best_f1["gates"],4),
            f1_contributes_to_joint_frontier=any(r["family"]=="F1" for r in nondominated),
            f2_contributes_to_joint_frontier=any(r["family"]=="F2" for r in nondominated)))
    def save(name,items):
        with (OUT/name).open("w",newline="") as f:
            w=csv.DictWriter(f,fieldnames=list(items[0]));w.writeheader();w.writerows(items)
    save("cross_family_measured_summary.csv",summary)
    save("cross_family_measured_pareto.csv",frontier)
    plotted=[m for m in (5,20,40,80,163,233,571) if m in degrees]
    fig,axes=plt.subplots(2,4,figsize=(16,8),layout="constrained")
    axes=axes.ravel()
    for ax,m in zip(axes,plotted):
        for family,marker in [("F1","s"),("F2","o")]:
            ps=[r for r in rows[m] if r["family"]==family]
            ax.scatter([r["gates"] for r in ps],[r["depth"] for r in ps],
                label=family,marker=marker,s=30,alpha=.65)
        ps=sorted((r for r in frontier if r["m"]==m),key=lambda r:r["gates"])
        ax.plot([r["gates"] for r in ps],[r["depth"] for r in ps],color="black",linewidth=1)
        ax.set(title=f"m={m}",xlabel="XOR gates",ylabel="XOR depth")
        ax.legend()
    for ax in axes[len(plotted):]:ax.set_visible(False)
    fig.savefig(OUT/"cross_family_measured_pareto.pdf")
    plt.close(fig)
    meta=dict(degrees=degrees,f1_circuits=len(f1),
        f1_only_degrees=sorted(f1_degrees-f2_degrees),
        f1_circuits_at_common_degrees=sum(int(r["m"]) in degrees for r in f1),
        f1_on_joint_frontier=sum(r["f1_contributes_to_joint_frontier"] for r in summary),
        f2_on_joint_frontier=sum(r["f2_contributes_to_joint_frontier"] for r in summary),
        limitation="F1 Conta-XOR/Paar only; BCP depth unmeasured")
    (OUT/"cross_family_measured_metadata.json").write_text(json.dumps(meta,indent=2)+"\n")
    print(json.dumps(meta))
if __name__=="__main__":main()
