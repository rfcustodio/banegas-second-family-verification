import json, math, statistics
sec=[tuple(map(int,l.split())) for l in open('sec.txt')]
fst=[tuple(map(int,l.split())) for l in open('fst.txt')]
tri={int(a):int(b) for a,b in (l.split() for l in open('tri.txt'))}
SPEC={(2,1):(6,7),(3,1):(10,12),(4,1):(14,15),(5,1):(16,18),(3,2):(16,18)}
def base(b,c):
    g=math.gcd(b,c); return (b//g,c//g),g
def cost2(m,b,c):
    (bp,cp),g=base(b,c)
    if (bp,cp) in SPEC:
        R2,R1=SPEC[(bp,cp)]; return (g-1)*R1+R2
    return 3*m-c-3
F2={}; F2gen={}
for m,b,c in sec:
    v=cost2(m,b,c)
    if m not in F2 or v<F2[m][0]: F2[m]=(v,b,c)
    if base(b,c)[0] not in SPEC:
        v=3*m-c-3
        if m not in F2gen or v<F2gen[m][0]: F2gen[m]=(v,b,c)
F1={}
for m,b,c in fst:
    v=(12*m)//5-1 if b==2*c else 3*m-2
    if m not in F1 or v<F1[m][0]: F1[m]=(v,b,c)
T={m for m,k in tri.items() if k>0 and 5<=m<=1100}
deg=set(range(5,1101)); noT=deg-T
print("irreducible second family:",len(sec))
print("degrees second/first:",len(F2),len(F1))
both=[m for m in F2 if m in F1]
print("both:",len(both))
better=[m for m in both if F2[m][0]<F1[m][0]]; worse=[m for m in both if F2[m][0]>F1[m][0]]; tie=[m for m in both if F2[m][0]==F1[m][0]]
print("second cheaper:",len(better),"worse:",worse,"tie:",tie)
print("mean saving over cheaper: %.4f"%statistics.mean((F1[m][0]-F2[m][0])/F1[m][0] for m in better))
# closed-form only (old version) comparison
F2c={}
for m,b,c in sec:
    v=3*m-c-3
    (bp,cp),g=base(b,c)
    if (bp,cp)==(2,1): v=7*g-1   # equally spaced, literature
    if m not in F2c or v<F2c[m][0]: F2c[m]=(v,b,c)
bc=[m for m in both if F2c[m][0]<F1[m][0]]; print("old (closed form + equally spaced) cheaper:",len(bc),[m for m in both if F2c[m][0]>=F1[m][0]])
print("degrees without trinomial:",len(noT))
print("covered second/first:",len(noT&set(F2)),len(noT&set(F1)))
print("second only:",len(noT&(set(F2)-set(F1))),"both:",len(noT&set(F2)&set(F1)),"first only:",len(noT&(set(F1)-set(F2))),"neither:",len(noT-set(F2)-set(F1)))
for name,S in [("all 720 (best generic)",[m for m in F2gen]),("noT generic",[m for m in F2gen if m in noT])]:
    print("mean cost/bit best generic over",name,len(S),"%.4f"%statistics.mean(F2gen[m][0]/m for m in S))
print("mean cost/bit best (incl special) all:","%.4f"%statistics.mean(F2[m][0]/m for m in F2))
# compare with census.json
J=json.load(open('../data/census.json'))
jF2={int(k):v for k,v in J['F2'].items()}; jF1={int(k):v for k,v in J['F1'].items()}; jT=set(J['T'])
print("census.json F2 degrees equal:",set(jF2)==set(F2),"F1 degrees equal:",set(jF1)==set(F1),"T equal (5..1100):",{t for t in jT if 5<=t<=1100}==T)
d2=[(m,jF2[m],F2c[m]) for m in jF2 if jF2[m][0]!=F2c[m][0]]; print("F2 cost mismatches vs closed+eqsp:",d2[:10],len(d2))
d1=[(m,jF1[m],F1[m]) for m in jF1 if jF1[m][0]!=F1[m][0]]; print("F1 cost mismatches:",d1[:10],len(d1))
# m = 0 mod 8
m8=[m for m in F2 if m%8==0]; print("m=0 mod 8 with second-family member:",len(m8))
for ex in [(16,6,5),(48,18,15),(144,54,45)]: print(ex, ex in set(sec), "cost",3*ex[0]-ex[2]-3, "best at degree", F2[ex[0]])
# NIST
for m in [163,233,283,409,571]:
    print("NIST",m,"F2",F2.get(m),"F1",F1.get(m),"tri",tri.get(m))
# special irreducible list
sp=sorted((m,b,c) for m,b,c in sec if base(b,c)[0] in SPEC)
print("special irreducible:",len(sp))
for m,b,c in sp:
    (bp,cp),g=base(b,c); print(" ",m,b,c,(bp,cp),g,3*m-c-3,cost2(m,b,c),F2gen.get(m,(None,))[0], "tri" if m in T else "noTri")
json.dump({'F2':{m:list(v) for m,v in F2.items()},'F2gen':{m:list(v) for m,v in F2gen.items()},'F1':{m:list(v) for m,v in F1.items()},'T':sorted(T)},open('census_verified.json','w'))
