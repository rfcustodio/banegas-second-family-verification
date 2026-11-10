exec(open("exact_base.py").read().split("if __name__ == \"__main__\":")[0])
from pysat.formula import IDPool
src=open('slp_sat.py').read().split("if __name__ == '__main__':")[0]
src=src.replace("    with Cadical153(bootstrap_with=cl) as s:\n        return s.solve()","    with Cadical153(bootstrap_with=cl) as s:\n        ok=s.solve(); return (ok, set(l for l in s.get_model() if l>0) if ok else None, pool, T)")
ns={}; exec(src,ns)
def satprog(bp,cp,top,K):
    rows,n,k=strip_reduced(bp,cp,top)
    ok,model,pool,T=ns['decide'](rows,n,K-k)
    assert ok
    prog=[]
    for i in range(K-k):
        S=n+i
        pa=[p for p in range(S) if pool.id(('a',i,p)) in model][0]; pb=[p for p in range(S) if pool.id(('b',i,p)) in model][0]
        prog.append((pa,pb))
    return prog,rows,n,k
def compose(bp,cp,g,P1,P2):
    k=bp+2*cp; m=g*k; b=g*bp; c=g*cp
    f=(1<<m)|(1<<(b+c))|(1<<b)|(1<<c)|1
    out=[0]*m; gates=0
    for r in range(g):
        prog,rows,n,kk=(P2 if r==g-1 else P1)
        sig=[1<<(r+g*(kk+t)) for t in range(n)]   # high input t of the strip = global index r+g*(k+t)
        for p,q in prog: sig.append(sig[p]^sig[q]); gates+=1
        avail={}
        for v in sig: avail.setdefault(v,True)
        for i,row in enumerate(rows):
            # row: bitmask over strip high inputs
            v=0;t=0;x=row
            while x:
                if x&1: v^=1<<(r+g*(kk+t))
                x>>=1;t+=1
            if v and bin(v).count('1')>1: assert v in avail,("missing",i)
            lo=1<<(r+g*i); out[r+g*i]=v^lo; gates+= 1 if v else 0
    rows=[0]*m; x=1
    for j in range(2*m-1):
        if j>0:
            x<<=1
            if x>>m&1: x^=f
        y=x;i=0
        while y:
            if y&1: rows[i]|=1<<j
            y>>=1;i+=1
    return out==rows, gates
for (bp,cp,R2,R1) in [(4,1,14,15),(5,1,16,18)]:
    k=bp+2*cp
    P2=satprog(bp,cp,2*k-2,R2); P1=satprog(bp,cp,2*k-1,R1)
    bad=0; tot=0
    for g in range(1,1100//k+1):
        ok,gates=compose(bp,cp,g,P1,P2); tot+=1
        if not ok or gates!=(g-1)*R1+R2: bad+=1; print("BAD",g,ok,gates)
    print(f"f_({bp},{cp}): composed {tot} members (m<=1100), failures {bad}; bound {(R1)}*gamma-{R1-R2}",flush=True)
