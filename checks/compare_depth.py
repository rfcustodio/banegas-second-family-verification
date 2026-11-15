#!/usr/bin/env python3
"""Checks Section IX-F and Table 11 (depth of the reduction circuits) from
data/depth_members.csv and data/depth_census.csv, written by verification/depth_census.py
(which builds every circuit and checks it symbolically; about 4 minutes).
Standard library only.  Usage: python3 checks/compare_depth.py"""
import csv, sys
from collections import Counter, defaultdict
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
M = list(csv.DictReader(open(ROOT / 'data' / 'depth_members.csv')))
C = list(csv.DictReader(open(ROOT / 'data' / 'depth_census.csv')))
ok = True
def expect(label, got, want):
    global ok
    good = got == want; ok &= good
    print(f"  {'ok ' if good else 'BAD'} {label}: {got}" + ('' if good else f'  (paper: {want})'))

f1 = [r for r in M if r['family'] == '1']; f2 = [r for r in M if r['family'] == '2']
expect('first family: circuits, special (b = 2c) degrees, depths', (len(f1), sorted(int(r['m']) for r in f1 if r['construction'] == 'SP'), sorted({int(r['depth']) for r in f1})), (755, [5, 155], [3]))
expect('first family: gates are 3m-2, or 12m/5-1 when b = 2c', all(int(r['gates']) == (12 * int(r['m']) // 5 - 1 if r['construction'] == 'SP' else 3 * int(r['m']) - 2) for r in f1), True)
expect('second family: circuits, members, special members', (len(f2), len({(r['m'], r['b'], r['c']) for r in f2}), sum(r['construction'] == 'ST' for r in f2)), (4554, 1508, 15))
expect('greedy strip programs: maximum depth', max(int(r['depth']) for r in f2 if r['construction'] == 'SG'), 3)
# the census file agrees with the list of circuits
by = defaultdict(list)
for r in M: by[int(r['m']), r['family']].append((int(r['gates']), int(r['depth'])))
good = True
for r in C:
    m = int(r['m']); c2 = by[m, '2']; c1 = by.get((m, '1'))
    good &= int(r['f2_min_gates']) == min(c2)[0] and int(r['f2_min_depth']) == min(d for _, d in c2)
    good &= (r['f1_min_gates'] == '') == (c1 is None) and (c1 is None or int(r['f1_min_gates']) == min(c1)[0])
    for D in (3, 4, 5, 6, 8, 12):
        xs = [g for g, d in c2 if d <= D]; good &= r[f'f2_min_gates_depth_le_{D}'] == (str(min(xs)) if xs else '')
expect('depth_census.csv agrees with depth_members.csv', good, True)
# the first-family and second-family minima agree with the census of Table 6
import json
J = json.load(open(ROOT / 'data' / 'census_alg2.json'))
expect('minimum gates per degree agree with data/census_alg2.json (Table 6)',
       all(int(r['f2_min_gates']) == J['F2'][r['m']][0] and (r['f1_min_gates'] == '' or int(r['f1_min_gates']) == J['F1'][r['m']][0]) for r in C), True)
S = [r for r in C if r['f1_min_gates']]
expect('degrees with irreducible members of both families', len(S), 405)
expect('second family, smallest depth (depth: degrees)', dict(sorted(Counter(int(r['f2_min_depth']) for r in S).items())), {3: 2, 4: 292, 5: 69, 6: 21, 7: 13, 8: 5, 9: 2, 11: 1})
expect('degrees with smallest depth 3', sorted(int(r['m']) for r in S if r['f2_min_depth'] == '3'), [5, 155])
dd = sorted(int(r['f2_depth_at_min_gates']) for r in S)
expect('circuit with the fewest gates: degrees with depth <= 4, median depth', (sum(d <= 4 for d in dd), dd[len(dd) // 2]), (189, 7))
T11 = {3: (2, 2, '4.7'), 4: (294, 292, '8.9'), 5: (363, 346, '8.2'), 6: (384, 363, '8.0'), 8: (402, 373, '8.5'), 12: (405, 391, '8.7')}
for D, want in T11.items():
    sv = [100 * (int(r['f1_min_gates']) - int(r[f'f2_min_gates_depth_le_{D}'])) / int(r['f1_min_gates']) for r in S if r[f'f2_min_gates_depth_le_{D}']]
    pos = [s for s in sv if s > 0]
    expect(f'Table 11, D = {D}: degrees, with fewer gates, mean saving (%)', (len(sv), len(pos), f'{sum(pos)/len(pos):.1f}'), want)
sv = [100 * (int(r['f1_min_gates']) - int(r['f2_min_gates'])) / int(r['f1_min_gates']) for r in S]
expect('Table 11, no limit', (len(sv), sum(s > 0 for s in sv), f'{sum(sv)/len(sv):.1f}'), (405, 405, '9.7'))
def front(m):
    cs = sorted({(int(r['gates']), int(r['depth'])) for r in f2 if r['m'] == str(m)})
    return [x for x in cs if not any(y != x and y[0] <= x[0] and y[1] <= x[1] for y in cs)]
expect('m = 228: nondominated (gates, depth) of the second family', front(228), [(606, 152), (609, 20), (615, 16), (618, 10), (620, 4)])
expect('m = 228, 163, 571: first family (gates, depth)', [min(by[m, '1']) for m in (228, 163, 571)], [(682, 3), (487, 3), (1711, 3)])
expect('m = 163, 571: second family, fewest gates (gates, depth)', [min(by[m, '2']) for m in (163, 571)], [(440, 4), (1528, 4)])
expect('m = 975: members; low-depth variant (gates, depth); first family gates', (sorted({(r['b'], r['c']) for r in f2 if r['m'] == '975'}), [(int(r['gates']), int(r['depth'])) for r in f2 if r['m'] == '975' and r['construction'] == 'LD'], min(by[975, '1'])[0]), ([('973', '1')], [(9183, 11)], 2923))
print('DEPTH COMPARISON OK' if ok else 'DEPTH COMPARISON FAILED')
sys.exit(0 if ok else 1)
