"""Algorithm 2 (chain construction) as in the paper: generates the straight-line program,
checks it symbolically and reports gates and depth."""
import sys
def program(b, c):
    m=b+2*c; n=m-2
    sig=lambda t: ((t+1)//c)%3
    prog=[]; val={}; dep={}
    def inp(name, idx):
        val[name]=1<<idx; dep[name]=0
    for j in range(2*m-1): inp(('d',j), j)
    H=lambda s: ('d',m+s) if 0<=s<=n else None
    def Ename(t): return ('E',t) if t<=n-c else H(t)
    def Pname(k): return ('P',k) if k<=n-c else H(k-c)
    def gate(out, a, b_):
        ops=[o for o in (a,b_) if o is not None]
        if len(ops)==1: val[out]=val[ops[0]]; dep[out]=dep[ops[0]]; return
        val[out]=val[ops[0]]^val[ops[1]]; dep[out]=max(dep[ops[0]],dep[ops[1]])+1; prog.append((out,ops[0],ops[1]))
    for i in range(n-c, -1, -1):
        if i>=2*c-1 and sig(i)!=1: gate(('P',i), H(i-c), Ename(i+c))
        if sig(i)!=2: gate(('E',i), H(i), Pname(i+2*c))
    for k in range(2*c-1, n-c+1):
        if sig(k)==1: gate(('P',k), Ename(k-c), Ename(k))
    U={}
    for k in range(m):
        if k<=c-2: gate(('U',k), ('E',k), H(k+b+c))
        elif k==c-1: val[('U',k)]=val[Ename(k)]; dep[('U',k)]=dep[Ename(k)]
        elif k<=2*c-2: gate(('U',k), ('U',k-c), Ename(k))
        elif k<=n-c: val[('U',k)]=val[('P',k)]; dep[('U',k)]=dep[('P',k)]
        else: val[('U',k)]=val[H(k-c)]; dep[('U',k)]=0
    for i in range(m):
        gate(('t',i), ('d',i), ('U',i))
        if i>=b: gate(('r',i), ('t',i), ('U',i-b))
        else: val[('r',i)]=val[('t',i)]; dep[('r',i)]=dep[('t',i)]
    return prog, val, dep, m
def check(b,c):
    prog,val,dep,m=program(b,c)
    f=(1<<m)|(1<<(b+c))|(1<<b)|(1<<c)|1
    rows=[0]*m; r=1
    for j in range(2*m-1):
        if j: 
            r<<=1
            if r>>m&1: r^=f
        x=r;i=0
        while x:
            if x&1: rows[i]|=1<<j
            x>>=1;i+=1
    ok=all(val[('r',i)]==rows[i] for i in range(m))
    N=c*((b+c)//(3*c))+max(0,(b+c)%(3*c)-2*c)
    return ok,len(prog),3*m-3-N,max(dep[('r',i)] for i in range(m))
if __name__=='__main__':
    b,c=int(sys.argv[1]),int(sys.argv[2])
    print(check(b,c))
    if len(sys.argv)>3:
        prog,_,_,_=program(b,c)
        for g in prog: print(g)
