#!/usr/bin/env python3
"""Complete per-degree published-formula comparison F1 vs F2 (m <= 1100).

This is an AREA comparison of construction formulas, NOT an SLP-depth study.
"""
import csv
import math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"experiments"/"results"
BASE={(2,1):(6,7),(3,1):(10,12),(4,1):(14,15),(5,1):(16,18),(3,2):(16,18)}
def pairs(name):
    for line in (ROOT/"data"/name).read_text().splitlines():
        if line.strip() and not line.startswith("#"):
            m,b,c=map(int,line.split())
            if 5<=m<=1100:yield m,b,c
def f2cost(m,b,c):
    n=c*((b+c)//(3*c))+max(0,(b+c)%(3*c)-2*c)
    values=[("F2 closed form",3*m-c-3),("F2 chain",3*m-3-n)]
    g=math.gcd(b,c);base=(b//g,c//g)
    if base in BASE:
        r2,r1=BASE[base]
        values.append(("F2 SAT-certified strip area",(g-1)*r1+r2))
    return values
def main():
    OUT.mkdir(parents=True,exist_ok=True)
    f1={}
    for m,b,c in pairs("fam1_irr.txt"):
        assert m==2*b+c
        v=12*m//5-1 if b==2*c else 3*m-2
        if m not in f1 or (v,b,c)<f1[m]:f1[m]=(v,b,c)
    f2={}
    for m,b,c in pairs("fam2_irr.txt"):
        assert m==b+2*c
        for method,v in f2cost(m,b,c):
            if m not in f2 or (v,b,c,method)<f2[m]:f2[m]=(v,b,c,method)
    common=sorted(set(f1)&set(f2))
    rows=[]
    for m in common:
        a,b,c=f1[m];d,e,f,method=f2[m]
        rows.append(dict(m=m,f1_formula_xors=a,f1_b=b,f1_c=c,
                         f2_formula_xors=d,f2_b=e,f2_c=f,f2_method=method,
                         f2_minus_f1=d-a,f2_improves=d<a))
    assert len(f1)==502 and len(f2)==720
    with (OUT/"f1_f2_formula_comparison.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    print("F1 degrees",len(f1),"F2 degrees",len(f2),"overlap",len(common),
          "F2 strictly better",sum(r["f2_improves"] for r in rows))
if __name__=="__main__":main()
