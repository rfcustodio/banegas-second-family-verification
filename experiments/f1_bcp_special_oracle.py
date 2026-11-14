#!/usr/bin/env python3
"""Independent regression oracle for the BCP 2019 special family b=2c.

The published Algorithm 3 transcription uses T1[c-1] although T1 is
initialized only for 0..c-2. Do not silently treat it as a verified SLP.
This oracle verifies all columns of any proposed special-case SLP exactly
over GF(2), without randomized sampling.
"""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"generator"))
from contaxor import pmod

def exact_check(c,prog,rows,n):
    m=5*c
    assert n==2*m-1 and len(rows)==m
    f=(1<<m)|(1<<(3*c))|(1<<(2*c))|(1<<c)|1
    masks={j:1<<j for j in range(n)}
    for w,u,v in prog:
        assert w not in masks and u in masks and v in masks
        masks[w]=masks[u]^masks[v]
    for i,row in enumerate(rows):
        mask=0
        for j in row:mask^=masks[j]
        expected=0
        for j in range(n):
            if (pmod(1<<j,f)>>i)&1:expected|=1<<j
        if mask!=expected:
            raise AssertionError((c,i,mask^expected))
    return True

def test_oracle():
    for c in (1,2,31):
        m=5*c;n=2*m-1
        f=(1<<m)|(1<<(3*c))|(1<<(2*c))|(1<<c)|1
        rows=[set() for _ in range(m)]
        for j in range(n):
            r=pmod(1<<j,f)
            for i in range(m):
                if (r>>i)&1:rows[i].add(j)
        assert exact_check(c,[],rows,n)
        bad=[set(r) for r in rows]
        bad[0].symmetric_difference_update({0})
        try:exact_check(c,[],bad,n)
        except AssertionError:pass
        else:raise AssertionError("Oracle failed to detect a corrupted output")
    # Literal indexing of published Algorithm 3 is not well-formed for c>=1.
    for c in (1,2,31):
        initialized=set(range(max(0,c-1)))
        assert c-1 not in initialized

if __name__=="__main__":
    test_oracle()
    print("BCP special-family exact GF(2) oracle verified for c=1,2,31;")
    print("published Algorithm 3 T1[c-1] indexing remains unresolved.")
