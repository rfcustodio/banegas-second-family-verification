#!/usr/bin/env python3
"""Independent first-family Conta-XOR/Paar baseline on selected degrees.

IMPORTANT: This is NOT the BCP circuit. BCP is represented by a published
area formula only, with no depth estimate until its exact SLP is implemented.
"""
import csv
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"generator"))
from contaxor import matriz_reducao,conta_xor,profundidade,verifica
OUT=ROOT/"experiments"/"results"
DEGREES={5,8,9,11,12,13,16,23,24,25,27,29,30,36,37,40,45,46,47,48,52,53,55,60,62,63,65,72,76,80,81,83,85,89,90,93,94,95,97,99,163,233,409,571}

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    result=[]
    for line in (ROOT/"data"/"fam1_irr.txt").read_text().splitlines():
        if not line.strip() or line.startswith("#"):continue
        m,b,c=map(int,line.split())
        if m not in DEGREES:continue
        assert m==2*b+c
        f=(1<<m)|(1<<(b+c))|(1<<b)|(1<<c)|1
        rows,n=matriz_reducao(f)
        gates,prog,fin=conta_xor(rows,n)
        assert verifica(prog,fin,f,testes=50),(m,b,c)
        result.append(dict(m=m,b=b,c=c,method="F1 Conta-XOR/Paar heuristic",
                           gates=gates,depth=profundidade(prog,fin,n),
                           bcp_formula=(12*m//5-1 if b==2*c else 3*m-2),
                           bcp_depth="unknown"))
    assert result,"No first-family polynomials at selected degrees"
    with (OUT/"f1_contaxor_baseline.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(result[0]));w.writeheader();w.writerows(result)
    print("Verified",len(result),"F1 Conta-XOR/Paar baseline SLPs")
if __name__=="__main__":main()
