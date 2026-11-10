import time
exec(open('slp_sat.py').read().split("if __name__ == '__main__':")[0])
def strip_reduced(bp,cp,top):
    k=bp+2*cp; ex=[bp+cp,bp,cp,0]; col=[0]*k; col[0]=1; rows=[0]*k
    for j in range(top+1):
        if j>0:
            t=col[k-1]; col=[0]+col[:-1]
            if t:
                for e in ex: col[e]^=1
        if j>=k:
            for i in range(k):
                if col[i]: rows[i]|=1<<(j-k)
    # low inputs j<k each appear only in output j -> Red = k + Red(rows)
    return rows, top-k+1, k
if __name__ == "__main__":
  for (bp,cp,R1) in [(2,1,7),(3,1,12),(4,1,15),(5,1,18),(3,2,18)]:
      rows,n,k=strip_reduced(bp,cp,2*(bp+2*cp)-1)
      for K in (R1-k, R1-k-1):
          t=time.time(); r=decide(rows,n,K)
          print(f"G=f_({bp},{cp}) R1 with {K+k} gates: {'SAT' if r else 'UNSAT'} ({time.time()-t:.1f}s)",flush=True)
          if not r: break
