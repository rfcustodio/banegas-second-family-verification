import math
SPEC={(2,1),(3,1),(4,1),(5,1),(3,2)}
D={}
for l in open('../data/paar150.txt'):
    v=list(map(int,l.split())); D[(v[0],v[2],v[3])]=v
R=[tuple(map(int,l.split())) for l in open('g150.txt')]
print("pairs",len(R))
mism=[(m,b,c) for m,b,c,dx,cx,br,cl in R if D[(m,b,c)][4]!=dx or D[(m,b,c)][5]!=cx]
print("dXOR/CX mismatches vs paar150.txt:",len(mism),mism[:5])
gen=[r for r in R if (lambda g:(r[1]//g,r[2]//g))(math.gcd(r[1],r[2])) not in SPEC]
print("generic",len(gen))
a=[r for r in gen if r[6]>r[4] or r[6]>r[5]]; print("(a) closed form more expensive than lexicographic or random:",len(a),a[:5])
# also against data random column
a2=[r for r in gen if r[6]>D[(r[0],r[1],r[2])][7]]; print("(a) vs data random column:",len(a2))
lt=[r for r in gen if r[1]<2*r[2]]; print("(b) b<2c:",len(lt),"all CX=2m+3c-3:",all(r[4]==2*r[0]+3*r[2]-3 for r in lt))
mid=[r for r in gen if 2*r[2]<r[1]<6*r[2]]; print("(c) 2c<b<6c:",len(mid),"all CX=closed:",all(r[4]==r[6] for r in mid))
hi=[r for r in gen if r[1]>=6*r[2]]; ex=[r for r in hi if r[4]>r[6]]
print("(d) b>=6c:",len(hi),"CX>closed:",len(ex),"max diff:",max(r[4]-r[6] for r in hi), "any CX<closed:",any(r[4]<r[6] for r in hi))
# random improvements: mine and data
imp=[r for r in gen if r[5]<r[4]]; print("random improved (mine):",len(imp),"all b>=6c:",all(r[1]>=6*r[2] for r in imp),"max improvement:",max((r[4]-r[5] for r in imp),default=0),"closed gap eliminated:",sum(1 for r in imp if r[4]>r[6] and r[5]<=r[6]))
dimp=[r for r in gen if D[(r[0],r[1],r[2])][7]<r[4]]
print("random improved (data):",len(dimp),"all b>=6c:",all(r[1]>=6*r[2] for r in dimp),"max:",max(r[4]-D[(r[0],r[1],r[2])][7] for r in dimp),"gap eliminated:",sum(1 for r in dimp if r[4]>r[6] and D[(r[0],r[1],r[2])][7]<=r[6]))
# b<2c region max diff
print("max gain b<2c:",max((r[4]-r[6],r) for r in lt))
# special members vs strip bound
SB={(2,1):(6,7),(3,1):(10,12),(4,1):(14,16),(5,1):(17,19),(3,2):(16,18)}
sp=[r for r in R if r not in gen]
rows=[]
for m,b,c,dx,cx,br,cl in sp:
    g=math.gcd(b,c); key=(b//g,c//g); R2,R1=SB[key]; bound=(g-1)*R1+R2
    rows.append((key,g,m,cx,br,bound,cl))
from collections import defaultdict
agg=defaultdict(list)
for key,g,m,cx,br,bound,cl in rows: agg[key].append((g,cx,br,bound,cl))
for key in agg:
    L=sorted(agg[key]); 
    print(key,"lex==bound:",sum(1 for g,cx,br,bd,cl in L if cx==bd),"/",len(L),"rand==bound:",sum(1 for g,cx,br,bd,cl in L if br==bd),"min(lex,rand)<bound:",sum(1 for g,cx,br,bd,cl in L if min(cx,br)<bd),"sample",L[:4])
b3=[r for r in sp if r[1]==3*r[2]]; print("b=3c: CX==12m/5-2:",all(5*(r[4]+2)==12*r[0] for r in b3), [(r[0],r[4]) for r in b3][:6])
