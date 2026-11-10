"""Census of Section IX with both constructions (closed form and chain construction)."""
import math, statistics, json, os
here=os.path.dirname(os.path.abspath(__file__))
V=os.path.join(here,'..','verification')   # sec.txt, fst.txt, tri.txt written there by run_all.sh
sec=[tuple(map(int,l.split())) for l in open(os.path.join(V,'sec.txt'))]
fst=[tuple(map(int,l.split())) for l in open(os.path.join(V,'fst.txt'))]
tri={int(a):int(b) for a,b in (l.split() for l in open(os.path.join(V,'tri.txt')))}
SPEC={(2,1):(6,7),(3,1):(10,12),(4,1):(14,15),(5,1):(16,18),(3,2):(16,18)}
def N(b,c): return c*((b+c)//(3*c))+max(0,(b+c)%(3*c)-2*c)
def base(b,c):
    g=math.gcd(b,c); return (b//g,c//g),g
def a1(m,b,c): return 3*m-c-3
def a2(m,b,c): return 3*m-3-N(b,c)
def spec(m,b,c):
    (bp,cp),g=base(b,c)
    if (bp,cp) in SPEC: R2,R1=SPEC[(bp,cp)]; return (g-1)*R1+R2
    return 10**9
def best(m,b,c,new): return min(a1(m,b,c),spec(m,b,c),a2(m,b,c) if new else 10**9)
F1={}
for m,b,c in fst:
    v=(12*m)//5-1 if b==2*c else 3*m-2
    if m not in F1 or v<F1[m][0]: F1[m]=(v,b,c)
T={m for m,k in tri.items() if k>0 and 5<=m<=1100}
noT=set(range(5,1101))-T
res={}
for new in (False,True):
    F2={}; G={}
    for m,b,c in sec:
        v=best(m,b,c,new)
        if m not in F2 or v<F2[m][0]: F2[m]=(v,b,c)
        if base(b,c)[0] not in SPEC:
            v=min(a1(m,b,c),a2(m,b,c) if new else 10**9)
            if m not in G or v<G[m][0]: G[m]=(v,b,c)
    res[new]=(F2,G)
    both=[m for m in F2 if m in F1]
    better=[m for m in both if F2[m][0]<F1[m][0]]
    print("NEW" if new else "OLD","degrees",len(F2),"both",len(both),"cheaper",len(better),
          "mean saving %.4f"%statistics.mean((F1[m][0]-F2[m][0])/F1[m][0] for m in better),
          "max saving %.4f"%max((F1[m][0]-F2[m][0])/F1[m][0] for m in better), "min %.4f"%min((F1[m][0]-F2[m][0])/F1[m][0] for m in better))
    print("  mean cost/bit best generic all %d: %.4f; noT %d: %.4f; best incl special %.4f"%(len(G),statistics.mean(G[m][0]/m for m in G),
          len([m for m in G if m in noT]),statistics.mean(G[m][0]/m for m in G if m in noT),statistics.mean(F2[m][0]/m for m in F2)))
    print("  mean saving noT both: %.4f"%statistics.mean((F1[m][0]-F2[m][0])/F1[m][0] for m in both if m in noT))
    for m in [163,233,409,571]: print("  NIST",m,F2.get(m))
F2o,Go=res[False]; F2n,Gn=res[True]
imp=[m for m in F2n if F2n[m][0]<F2o[m][0]]
print("degrees improved",len(imp),"of",len(F2n),"; noT improved",len([m for m in imp if m in noT]))
rel=sorted(((F2o[m][0]-F2n[m][0])/F2o[m][0],m,F2o[m],F2n[m]) for m in imp)
print("max rel",rel[-5:]); print("mean rel over improved %.4f"%statistics.mean(r for r,*_ in rel))
# how often is best member from alg2 (b>=4c+1)
fromA2=[m for m in F2n if a2(*((m,)+F2n[m][1:]))==F2n[m][0] and a2(m,*F2n[m][1:])<a1(m,*F2n[m][1:])]
print("best member uses alg2 in",len(fromA2))
# examples of 0 mod 8
for ex in [(16,6,5),(48,18,15),(144,54,45)]: print(ex,F2n[ex[0]],F2o[ex[0]])
# per-member: how many irreducible members improved
print("irreducible members improved",sum(1 for m,b,c in sec if a2(m,b,c)<min(a1(m,b,c),spec(m,b,c))),"of",len(sec))
json.dump({'F2':{m:list(v) for m,v in F2n.items()},'F2gen':{m:list(v) for m,v in Gn.items()},'F2_alg1':{m:list(v) for m,v in F2o.items()},'F1':{m:list(v) for m,v in F1.items()},'T':sorted(T)},open(os.path.join(here,'..','data','census_alg2.json'),'w'))
# special member table generic column
for m in [20,54,100,155,162,378,486,500]: print("spec deg",m,"generic old",Go.get(m),"new",Gn.get(m))
# m=5: first family
print(F2n[5],F1.get(5), F2n[155], F1.get(155))
