#!/usr/bin/env python3
"""Measured depths for heuristic strip SLPs of irreducible special members.

These are NOT the SAT-certified minimum-area strip programs. Counts and
depths are obtained from the same concrete SLP, and outputs are symbolically
verified using the existing generator/strips.py implementation.
"""
import csv
import math
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"generator"))
from strips import BASE, rows_of, fam, greedy, cost, compose_and_check, TMP

OUT=ROOT/"experiments"/"results"

def depth(prog,k,top):
    gates,rows=prog
    d={j:0 for j in range(top+1)}
    for t,a,b in gates:
        d[t]=max(d[a],d[b])+1
    depths=[]
    for row in rows:
        if not row:
            depths.append(0)
            continue
        # Depth-minimizing binary association for the same output XOR count.
        # Reassociate only the final row, leaving the shared intermediate SLP fixed.
        levels=sorted(d[v] for v in row)
        while len(levels)>1:
            a,b=levels.pop(0),levels.pop(0)
            nxt=max(a,b)+1
            pos=0
            while pos<len(levels) and levels[pos]<nxt:
                pos+=1
            levels.insert(pos,nxt)
        depths.append(levels[0])
    return max(depths)

def best_program(bp,cp,top,runs=20):
    k=bp+2*cp
    rows=rows_of(fam(bp,cp),top)
    return min((greedy(rows,None),*(greedy(rows,s) for s in range(runs))),
               key=lambda p:(cost(p),depth(p,k,top)))

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    pairs={tuple(map(int,line.split())) for line in
           (ROOT/"data"/"fam2_irr.txt").read_text().splitlines()
           if line.strip() and not line.startswith("#")}
    cache={}
    result=[]
    for m,b,c in sorted(pairs):
        if not 5<=m<=1100: continue
        g=math.gcd(b,c)
        base=(b//g,c//g)
        if base not in BASE: continue
        if base not in cache:
            bp,cp=base;k=bp+2*cp
            p1=best_program(bp,cp,2*k-1)
            p2=best_program(bp,cp,2*k-2)
            cache[base]=(p1,p2,depth(p1,k,2*k-1),depth(p2,k,2*k-2))
        p1,p2,d1,d2=cache[base]
        ok,gates,_=compose_and_check(*base,g,p1,p2)
        assert ok,(m,b,c)
        assert gates==(g-1)*cost(p1)+cost(p2)
        sat2,sat1=BASE[base]
        sat_area=(g-1)*sat1+sat2
        assert gates>=sat_area,(m,b,c,gates,sat_area)
        result.append(dict(m=m,b=b,c=c,base_b=base[0],base_c=base[1],
                           gamma=g,heuristic_gates=gates,
                           heuristic_depth=max(d1,d2) if g>1 else d2,
                           sat_optimal_area=sat_area,
                           area_gap=gates-sat_area,
                           verified=True))
    assert len(result)==15, f"Unexpected number of special irreducible members: {len(result)}"
    with (OUT/"special_heuristic_slps.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(result[0]));w.writeheader();w.writerows(result)
    print("Symbolically verified",len(result),"special-member heuristic strip SLPs")
    print("Warning: heuristic_depth is NOT the depth of SAT-optimal area circuits")

if __name__=="__main__":main()
