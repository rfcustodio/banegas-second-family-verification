#!/usr/bin/env python3
"""Exact BCP special-case reduction SLP, f=x^(5c)+x^(3c)+x^(2c)+x^c+1.

The strip construction is reconstructed independently from the 2015 MSc
dissertation, Eq. (5.28), and checked against polynomial long division.
For c>=1, its 12c-1 XORs have maximum XOR depth 3.

No irreducibility assumption is needed to verify the reduction identity.
"""
import argparse
import json

def build(c):
    if c < 1:
        raise ValueError("c must be positive")
    m = 5*c
    masks = [1 << i for i in range(2*m-1)]
    depths = [0]*(2*m-1)
    ops = []
    def xor(a,b):
        idx = len(masks)
        masks.append(masks[a]^masks[b])
        depths.append(max(depths[a],depths[b])+1)
        ops.append((idx,a,b))
        return idx
    out = []
    for j in range(c):
        a = lambda k: j+k*c
        t = xor(a(5),a(6))
        # The last strip lacks the coefficient d_(9c+j).
        u = xor(a(7),a(9)) if j < c-1 else a(7)
        y0 = xor(xor(a(0),a(8)),xor(a(5),a(7)))
        y1 = xor(a(1),xor(t,u))
        y2 = xor(a(2),t)
        y3 = xor(a(3),xor(t,a(8)))
        y4 = xor(a(4),xor(a(6),u))
        out.extend([(j+k*c, y) for k,y in enumerate([y0,y1,y2,y3,y4])])
    assert len(ops) == 12*c-1, (c,len(ops))
    assert max(depths[i] for _,i in out) <= 3
    return m,masks,depths,ops,dict(out)

def reference(m):
    f = (1<<(5*(m//5))) | (1<<(3*(m//5))) | (1<<(2*(m//5))) | (1<<(m//5)) | 1
    cols=[]
    for i in range(2*m-1):
        r=1<<i
        while r.bit_length()>m:
            r ^= f << (r.bit_length()-1-m)
        cols.append(r)
    return [sum(1<<i for i,col in enumerate(cols) if (col>>j)&1) for j in range(m)]

def check(c):
    m,masks,depths,ops,out=build(c)
    expected=reference(m)
    assert [masks[out[j]] for j in range(m)] == expected, "symbolic reduction mismatch"
    return {"c":c,"m":m,"xor_gates":len(ops),"xor_depth":max(depths[out[j]] for j in range(m)),
            "symbolically_verified":True}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--max-c",type=int,default=220)
    p.add_argument("--json",action="store_true")
    a=p.parse_args()
    results=[check(c) for c in range(1,a.max_c+1)]
    if a.json:
        print(json.dumps({"count":len(results),"first":results[:3],"last":results[-1]},indent=2))
    else:
        print(f"Verified {len(results)} special BCP circuits, c=1..{a.max_c}; "
              f"each has 12c-1 XORs and depth <=3")

if __name__=="__main__":
    main()
