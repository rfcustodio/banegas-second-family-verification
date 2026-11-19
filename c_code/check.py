#!/usr/bin/env python3
# usage: ./bench --vectors --tests 5 > vectors.txt ; python3 check.py vectors.txt
import sys
def bits(x): return [i for i in range(x.bit_length()) if (x>>i)&1]
def mul(a,b):
    r=0
    for i in bits(a): r ^= b<<i
    return r
def mod(a,f):
    m=f.bit_length()-1
    for d in range(a.bit_length()-1,m-1,-1):
        if (a>>d)&1: a ^= f<<(d-m)
    return a
def pack(ws): return sum(w<<(64*i) for i,w in enumerate(ws))
ok=True
for ln in open(sys.argv[1]):
    t=ln.split()
    #print("t = {}".format(t))
    if t[0]!='V': continue
    m,ne=int(t[1]),int(t[2]); e=[int(x) for x in t[3:3+ne]]; W=(m+63)//64
    o=3+ne; a=pack([int(x,16) for x in t[o:o+W]])
    b=pack([int(x,16) for x in t[o+W:o+2*W]]); r=pack([int(x,16) for x in t[o+2*W:o+3*W]])
    f=(1<<m)|1
    for x in e: f|=1<<x
    want=mod(mul(a,b),f)
    if want!=r: ok=False; print("MISMATCH m=%d"%m)
print("all vectors match" if ok else "FAILURES")