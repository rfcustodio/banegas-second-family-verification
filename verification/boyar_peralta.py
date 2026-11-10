import itertools, random
def rows(m,ex):
    col=[0]*m; col[0]=1; R=[0]*m
    for j in range(2*m-1):
        if j>0:
            top=col[m-1]; col=[0]+col[:-1]
            if top:
                for e in ex[1:]: col[e]^=1
        for i in range(m):
            if col[i]: R[i]|=1<<j
    return R, 2*m-1
def sums_upto(S,k):
    # dict level -> set of xors of exactly up to k distinct elements
    out={0}; frontier={0:frozenset()}
    cur={0}
    allsums={0}
    layer={(0,-1)}
    res=set([0])
    # iterative: sums using increasing indices
    L=[(0,-1)]
    for depth in range(k):
        nl=[]
        for v,last in L:
            for i in range(last+1,len(S)):
                nl.append((v^S[i],i))
        L=nl
        res.update(v for v,_ in L)
    return res
def bp(m,ex,seed):
    rnd=random.Random(seed)
    T,N=rows(m,ex)
    T=[t for t in T if t]
    S=[1<<j for j in range(N)]
    Sset=set(S)
    dist=[bin(t).count('1')-1 for t in T]
    gates=0
    while any(dist):
        # immediate: a target at distance 1
        done=False
        for i,t in enumerate(T):
            if dist[i]==1:
                # find pair in S summing to t
                for a in S:
                    if (t^a) in Sset:
                        new=t; break
                done=True; break
        if not done:
            maxd=max(dist)
            sums={k:sums_upto(S,k) for k in range(0,maxd)}
            best=None; cands=[]
            for a,b in itertools.combinations(S,2):
                new=a^b
                if new in Sset: continue
                nd=[d-1 if d>0 and (t^new) in sums[d-1] else d for t,d in zip(T,dist)]
                key=(sum(nd), -sum(x*x for x in nd))
                if best is None or key<best: best=key; cands=[new]
                elif key==best: cands.append(new)
            new=rnd.choice(cands)
        S.append(new); Sset.add(new); gates+=1
        sums={k:sums_upto(S,k) for k in range(0,max(dist))}
        dist=[ (d-1 if d>0 and (t^new) in sums[d-1] else d) for t,d in zip(T,dist)]
    return gates
for name,m,ex in [("f_{5,2}",9,[9,7,5,2,0]),("f_{4,3}",10,[10,7,4,3,0]),("f_{3,2}",7,[7,5,3,2,0])]:
    res=[bp(m,ex,s) for s in range(10)]
    print(name,"m=",m,"BP runs:",res,"best",min(res),"closed",3*m-ex[3]-3)
