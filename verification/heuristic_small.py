"""'heuristic' column of Table 5: best of the greedy algorithm (lexicographic ties and
500 randomized runs, ./greedy) and of 10 runs of the Boyar-Peralta heuristic."""
import subprocess, re
exec(open('boyar_peralta.py').read().split('for name,m,ex in')[0])
for (b, c) in [(2,1),(3,1),(4,1),(5,1),(3,2),(6,1),(5,2),(7,1),(8,1),(7,2),(9,1)]:
    m = b + 2*c
    out = subprocess.run(['./greedy', 'one', '500', str(m), str(b+c), str(b), str(c), '0'],
                         capture_output=True, text=True).stdout
    cx, rnd = map(int, re.search(r'CX=(\d+) bestRandom=(-?\d+)', out).groups())
    g = min(cx, rnd) if rnd >= 0 else cx
    bp_best = min(bp(m, [m, b+c, b, c, 0], s) for s in range(10))
    print(f"f_({b},{c}) m={m}: greedy {g}, Boyar-Peralta {bp_best}, heuristic {min(g, bp_best)}, closed form {3*m-c-3}")
