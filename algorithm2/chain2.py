"""Chain model including the bottom targets, with closed-form and new identities.
Chain inputs h_0..h_J; external input x (for type A). C_j = sum h_{j+3i}; E_j = C_j + C_{j+1};
P_j = C_{j-1}+C_{j+1}.  Type A targets: UA0 = E_0 + x, UA1 = P_1 + x, P_j (2<=j<=J-1).
Type B targets: E_0, P_j (1<=j<=J-1)."""
import sys
from pysat.examples.rc2 import RC2
from pysat.formula import WCNF
def model(J, typ):
    X_EXT = J+1
    h=lambda j: (1<<j) if 0<=j<=J else 0
    x=1<<X_EXT
    C={}
    for j in range(J,-1,-1): C[j]=h(j)^(C[j+3] if j+3<=J else 0)
    Cv=lambda j: C.get(j,0) if j>=0 else 0
    nodes={}; forms={}
    def node(nm,v,key): nodes[nm]=(v,key); forms[nm]=[]
    for j in range(J+1): node(('C',j),C[j],(j,3)); node(('E',j),Cv(j)^Cv(j+1),(j,2))
    for j in range(1,J+2): node(('P',j),Cv(j-1)^Cv(j+1),(j-1,1))
    if typ=='A':
        node(('Z',),Cv(0)^x,(0,2.5)); node(('UA0',),Cv(0)^Cv(1)^x,(0,0.75)); node(('UA1',),Cv(0)^Cv(2)^x,(0,0.5))
    def val(o):
        if o[0]=='h': return h(o[1])
        if o[0]=='x': return x
        return nodes[o][0] if o in nodes else 0
    def add(nm,ops):
        ops2=[o for o in ops if val(o)!=0]
        for o in ops2:
            if o[0] not in ('h','x'): assert nodes[o][1]>nodes[nm][1],(nm,o)
        v=0
        for o in ops2: v^=val(o)
        if v!=nodes[nm][0]: return
        forms[nm].append((tuple(ops2),max(0,len(ops2)-1)))
    for j in range(J+1):
        add(('C',j),[('h',j),('C',j+3)])
        add(('E',j),[('C',j),('C',j+1)]); add(('E',j),[('h',j),('P',j+2)])
    for j in range(1,J+2):
        add(('P',j),[('C',j-1),('C',j+1)]); add(('P',j),[('E',j-1),('E',j)]); add(('P',j),[('h',j-1),('E',j+1)])
    if typ=='A':
        add(('Z',),[('C',0),('x',)])
        add(('UA0',),[('Z',),('C',1)]); add(('UA0',),[('E',0),('x',)])
        add(('UA1',),[('Z',),('C',2)]); add(('UA1',),[('P',1),('x',)]); add(('UA1',),[('UA0',),('E',1)])
        targets=[('UA0',),('UA1',)]+[('P',j) for j in range(2,J)]
    else:
        targets=[('E',0)]+[('P',j) for j in range(1,J)]
    return nodes,forms,targets
def solve(J,typ):
    nodes,forms,targets=model(J,typ)
    vid={}
    def X(n):
        if n not in vid: vid[n]=len(vid)+1
        return vid[n]
    w=WCNF(); Y={}
    for nm,fl in forms.items():
        ys=[]
        for i,(ops,cost) in enumerate(fl):
            y=X(('y',nm,i)); ys.append(y); Y[y]=(nm,ops,cost)
            for o in ops:
                if o[0] not in ('h','x'): w.append([-y,X(o)])
            if cost: w.append([-y],weight=cost)
        w.append([-X(nm)]+ys)
    for t in targets:
        v=nodes[t][0]
        if v==0 or bin(v).count('1')==1: continue
        w.append([X(t)])
    with RC2(w) as r:
        mdl=r.compute(); cost=r.cost
    ms=set(l for l in mdl if l>0)
    return cost,[Y[y] for y in Y if y in ms]
def closed_chain(J,typ):
    # closed form restricted to one chain: comb gates + P gates + (Z,UA0,UA1 for type A)
    comb=max(0,J-2)                      # C_j for j<=J-3
    if typ=='A': return comb+1+2+max(0,J-2)   # Z, UA0, UA1, P_2..P_{J-1}
    else: return comb+max(0,J-1)+0            # E_0 = C_0+C_1 (1 gate) counted as U_{c-1}: add 1
if __name__=='__main__':
    for J in range(1,int(sys.argv[1])+1):
        a,_=solve(J,'A'); b,_=solve(J,'B')
        print(J,a,b,flush=True)
