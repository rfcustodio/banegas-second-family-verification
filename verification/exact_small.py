"""Exact minima of Table 5 (SAT): for each member, test the closed form minus 1 and 2 gates.
Red(f) = m + Red(R'), where R' is the reduction matrix restricted to the high inputs."""
import time
exec(open('slp_sat.py').read().split("if __name__ == '__main__':")[0])
for (m,b,c,Ks) in [(4,2,1,[6,5]),(5,3,1,[10,9]),(6,4,1,[14,13]),(7,5,1,[16,15]),(7,3,2,[16,15]),
                   (8,6,1,[19,18]),(9,5,2,[21,20]),(9,7,1,[22]),(10,8,1,[24]),(11,7,2,[27]),(11,9,1,[27])]:
    rows,n=reduced_targets(m,b,c)
    for K in Ks:
        t=time.time(); r=decide(rows,n,K-m)
        print(f"f_({b},{c}) m={m}: program with {K} gates: {'exists' if r else 'impossible'} ({time.time()-t:.1f}s)",flush=True)
