def depth(b,c):
    m=b+2*c;n=m-2;dC={}
    for t in range(n,-1,-1): dC[t]=dC[t+3*c]+1 if t+3*c<=n else 0
    dZ={i:dC[i]+1 for i in range(c-1)}
    dU={}
    for k in range(m):
        if k<=c-2: dU[k]=max(dZ[k],dC[k+c])+1
        elif k==c-1: dU[k]=max(dC[c-1],dC[2*c-1])+1
        elif k<=2*c-2: dU[k]=max(dZ[k-c],dC[k+c])+1
        elif k<=b+c-2: dU[k]=max(dC[k-c],dC[k+c])+1
        else: dU[k]=dC[k-c]
    d=0
    for i in range(m):
        x=dU[i]+1
        if i>=b: x=max(x,dU[i-b])+1
        d=max(d,x)
    return d
for b,c in [(71,46),(83,75),(201,16),(179,115),(265,72),(207,182),(359,106),(527,22)]: print(b+2*c,b,c,depth(b,c))
