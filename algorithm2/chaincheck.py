import chain2
bad=0
for J in range(1,1101):
    a,_=chain2.solve(J,'A'); b,_=chain2.solve(J,'B')
    fa = 3 if J==2 else -(-5*J//3); fb=(5*J-2)//3
    if a!=fa or b!=fb: bad+=1; print("MISMATCH",J,a,fa,b,fb,flush=True)
print("checked J<=1100, mismatches:",bad)
