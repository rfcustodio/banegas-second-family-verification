#!/usr/bin/env python3
"""Summarize measured F2 Pareto fronts without modifying published figures."""
import csv
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"experiments"/"results"

def read(name):
    with (OUT/name).open(newline="") as f:
        return list(csv.DictReader(f))

def main():
    s=read("f2_area_depth_summary.csv")
    p=read("pareto_f2.csv")
    assert len(s)==720
    assert len(p)==sum(int(r["pareto_points"]) for r in s)
    trade=[r for r in s if int(r["pareto_points"])>1]
    changed=[r for r in s if int(r["depth_at_minimum_area"])>int(r["minimum_depth"])]
    assert len(trade)==len(changed), "Frontier count and depth tradeoffs disagree"
    by={}
    for r in p: by.setdefault(int(r["m"]),[]).append(r)
    m=228
    pts=sorted(by[m],key=lambda r:int(r["gates"]))
    assert len(pts)==5
    summary={
      "degrees":len(s),
      "degrees_with_area_depth_tradeoff":len(trade),
      "tradeoff_fraction":len(trade)/len(s),
      "pareto_points":len(p),
      "area_winner_chain":sum(r["area_method"]=="F2 chain" for r in s),
      "depth_winner_closed_form":sum(r["depth_method"]=="F2 closed form" for r in s),
      "m228":[{"gates":int(r["gates"]),"depth":int(r["depth"]),
               "method":r["method"],"b":int(r["b"]),"c":int(r["c"])} for r in pts],
      "scope":"Only executable F2 closed-form and chain SLPs; no F1 or SAT-optimal strips",
      "limitations":"Area=number of XOR gates; depth=logical XOR levels; not physical timing"
    }
    (OUT/"pareto_analysis.json").write_text(json.dumps(summary,indent=2)+"\n")
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print(json.dumps(summary));return
    fig,ax=plt.subplots(figsize=(6.4,3.8))
    x=[int(r["gates"]) for r in pts]
    y=[int(r["depth"]) for r in pts]
    ax.plot(x,y,"o-",linewidth=1.3)
    for r,xx,yy in zip(pts,x,y):
        ax.annotate(r["method"].replace("F2 ",""),(xx,yy),xytext=(3,5),
                    textcoords="offset points",fontsize=7)
    ax.set(xlabel="XOR gates (actual generated SLP)",ylabel="XOR depth",
           title="Area-depth Pareto frontier for m = 228")
    ax.grid(alpha=.2);fig.tight_layout()
    fig.savefig(OUT/"pareto_m228.pdf");plt.close(fig)
    print(json.dumps(summary))

if __name__=="__main__": main()
