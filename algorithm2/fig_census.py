"""Figure 3 (fig_census.pdf): cost per bit of the best member of each family in degrees
without irreducible trinomials. Reads data/census_alg2.json (written by
census_alg2.py)."""
import json, matplotlib, os
matplotlib.use('Agg')
import matplotlib.pyplot as plt
BLUE, LIGHT, ORANGE, INK2 = '#2a78d6', '#a9c8ef', '#eb6834', '#52514e'
plt.rcParams.update({'font.size': 9, 'axes.edgecolor': '#bdbcb6', 'xtick.color': INK2, 'ytick.color': INK2,
                     'axes.spines.top': False, 'axes.spines.right': False, 'font.family': 'serif', 'pdf.fonttype': 42})
here = os.path.dirname(os.path.abspath(__file__))
J = json.load(open(os.path.join(here, '..', 'data', 'census_alg2.json')))
F2 = {int(k): v for k, v in J['F2'].items()}; F2o = {int(k): v for k, v in J['F2_alg1'].items()}
F1 = {int(k): v for k, v in J['F1'].items()}; T = set(J['T'])
fig, ax = plt.subplots(figsize=(6.2, 2.9))
m1 = [m for m in sorted(F1) if m not in T]; m2 = [m for m in sorted(F2) if m not in T]
ax.scatter(m1, [F1[m][0]/m for m in m1], s=6, color=ORANGE, label='first family (BCP), best member', zorder=2)
ax.scatter(m2, [F2o[m][0]/m for m in m2], s=6, color=LIGHT, label='second family, closed form only', zorder=3)
ax.scatter(m2, [F2[m][0]/m for m in m2], s=6, color=BLUE, label='second family, closed form or chain construction', zorder=4)
ax.axhline(8/3, color=INK2, lw=0.8, ls='--'); ax.text(1105, 8/3, r'$8/3$', va='center', fontsize=8)
ax.axhline(3, color=INK2, lw=0.8, ls=':'); ax.text(1105, 3, r'$3$', va='center', fontsize=8)
ax.set_xlabel('degree $m$ (only degrees without an irreducible trinomial)'); ax.set_ylabel('XORs per bit')
ax.set_ylim(2.3, 3.1); ax.set_xlim(0, 1100)
ax.legend(frameon=False, fontsize=7.5, loc='lower right')
fig.tight_layout(); fig.savefig(os.path.join(here, '..', 'paper', 'fig_census.pdf')); plt.close(fig)
print('ok')
