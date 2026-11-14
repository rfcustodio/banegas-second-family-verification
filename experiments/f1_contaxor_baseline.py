#!/usr/bin/env python3
"""First-family Conta-XOR/Paar baseline on m<=200 and selected larger degrees.

The BCP Eq14 SLP is measured separately in f1_bcp_measured.py.
All heuristic SLPs are checked symbolically, not just with random inputs.
"""
import csv
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"generator"))
from contaxor import matriz_reducao,conta_xor,profundidade,verifica
from f1_bcp_measured import verify_exact
OUT=ROOT/"experiments"/"results"
DEGREES={233,409,571}
MAX_EXHAUSTIVE_DEGREE=200

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    result=[]
    for line in (ROOT/"data"/"fam1_irr.txt").read_text().splitlines():
        if not line.strip() or line.startswith("#"):continue
        m,b,c=map(int,line.split())
        if m not in DEGREES and m>MAX_EXHAUSTIVE_DEGREE:continue
        assert m==2*b+c
        f=(1<<m)|(1<<(b+c))|(1<<b)|(1<<c)|1
        rows,n=matriz_reducao(f)
        gates,prog,fin=conta_xor(rows,n)
        assert verify_exact(prog,fin,f,n),(m,b,c)
        assert verifica(prog,fin,f,testes=50),(m,b,c)
        result.append(dict(m=m,b=b,c=c,method="F1 Conta-XOR/Paar heuristic",
                           gates=gates,depth=profundidade(prog,fin,n),
                           bcp_formula=(12*m//5-1 if b==2*c else 3*m-2),
                           bcp_depth=("unmeasured special Algorithm 3" if b==2*c else "3 (BCP Eq14)")))
    assert result,"No first-family polynomials at selected degrees"
    with (OUT/"f1_contaxor_baseline.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(result[0]));w.writeheader();w.writerows(result)
    print("Verified",len(result),"F1 Conta-XOR/Paar baseline SLPs")
if __name__=="__main__":main()
