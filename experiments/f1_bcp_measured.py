#!/usr/bin/env python3
"""BCP (Banegas-Custodio-Panario 2019) first-family reduction SLP.

Direct implementation of the shared T1/T2/T3/T4/T5 construction in Eq. (14),
Theorem 2, Journal of Cryptographic Engineering 9 (2019), pp. 359-373.
Valid for b>c>=1 and b != 2c. The optimized special b=2c
Algorithm 3 is deliberately NOT represented by this generic circuit.
DOI: 10.1007/s13389-018-0197-6
"""
import csv
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"generator"))
from contaxor import verifica,profundidade,pmod
OUT=ROOT/"experiments"/"results"

def bcp_slp(b,c):
    assert b>c>=1 and b!=2*c
    m=2*b+c
    n=2*m-1
    rows=[[i] for i in range(m)]
    prog=[]
    depths={i:0 for i in range(n)}
    def xor(u,v):
        w=n+len(prog)
        prog.append((w,u,v))
        depths[w]=max(depths[u],depths[v])+1
        return w
    # Shared T1(j), j=0,b,b+c, Eq. (14)
    for i in range(b-1):
        t=xor(i+2*b+c,i+3*b+2*c)
        for j in (0,b,b+c):
            rows[i+j].append(t)
    # T2 at four shifts
    for j in (b-1,b+c-1,2*b-1,2*b+c-1):
        rows[j].append(3*b+c-1)
    # T3 at three shifts
    for i in range(c):
        for j in (0,c,2*b):
            rows[i+j].append(i+3*b+c)
    # T4(c), T5(2c)
    for i in range(b-1):
        rows[i+c].append(i+2*b+c)
        rows[i+2*c].append(i+3*b+2*c)
    # Associate output XORs with shallowest signals first.
    # This is an explicit two-input gate SLP, not a formula-only depth.
    for row in rows:
        while len(row)>1:
            row.sort(key=lambda t:(depths[t],t))
            u=row.pop(0)
            v=row.pop(0)
            row.append(xor(u,v))
    assert all(len(row)==1 for row in rows)
    return prog,[set(row) for row in rows],n

def verify_exact(prog,rows,f,n):
    """Prove equality of linear maps over GF(2), for every possible input."""
    m=f.bit_length()-1
    masks={j:1<<j for j in range(n)}
    for w,u,v in prog:
        assert w not in masks and u in masks and v in masks
        masks[w]=masks[u]^masks[v]
    actual=[]
    for row in rows:
        acc=0
        for v in row:acc^=masks[v]
        actual.append(acc)
    expected=[0]*m
    for j in range(n):
        reduced=pmod(1<<j,f)
        while reduced:
            bit=reduced&-reduced
            i=bit.bit_length()-1
            expected[i]^=1<<j
            reduced^=bit
    assert actual==expected,("BCP symbolic mismatch",m)
    return True

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    data=[]
    for line in (ROOT/"data"/"fam1_irr.txt").read_text().splitlines():
        if not line.strip() or line.startswith("#"):continue
        m,b,c=map(int,line.split())
        if m>1100 or b==2*c:continue
        prog,rows,n=bcp_slp(b,c)
        f=(1<<m)|(1<<(b+c))|(1<<b)|(1<<c)|1
        gates=len(prog)
        depth=profundidade(prog,rows,n)
        assert gates==3*m-2,(m,b,c,gates,3*m-2)
        assert depth<=3,(m,b,c,depth)
        assert verify_exact(prog,rows,f,n),(m,b,c)
        assert verifica(prog,rows,f,testes=20),(m,b,c)
        data.append(dict(m=m,b=b,c=c,method="F1 BCP 2019 Eq14",
                         gates=gates,depth=depth,verified=True))
    assert data
    with (OUT/"f1_bcp_measured.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(data[0]));w.writeheader();w.writerows(data)
    print("BCP verified circuits",len(data),"degrees",len({r["m"] for r in data}))
if __name__=="__main__":main()
