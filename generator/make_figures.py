"""Regenerates paper/fig_gain.pdf (Figure 2) and paper/fig_census.pdf (Figure 3)
from data/paar150.txt and data/census.json.  Requires numpy and matplotlib.
Usage: python3 generator/make_figures.py"""
import json, matplotlib
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
DATA, PAPER = ROOT / 'data', ROOT / 'paper'
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
BLUE, ORANGE, AQUA, GRAY, INK, INK2 = '#2a78d6', '#eb6834', '#1baf7a', '#8a8984', '#0b0b0b', '#52514e'
plt.rcParams.update({'font.size': 9, 'axes.edgecolor': '#bdbcb6', 'xtick.color': INK2, 'ytick.color': INK2,
                     'axes.spines.top': False, 'axes.spines.right': False, 'font.family': 'serif', 'pdf.fonttype': 42})
spec = lambda b, c: b in (2*c, 3*c, 4*c, 5*c) or 2*b == 3*c
R = [list(map(int, l.split())) for l in open(DATA / 'paar150.txt')]
# ---- Fig A: Conta-XOR excess over the closed form vs b/c
fig, ax = plt.subplots(figsize=(6.2, 2.7))
xs = [b/c for m,a,b,c,*_ in R if not spec(b,c)]
ys = [p-(3*m-c-3) for m,a,b,c,dx,p,*_ in R if not spec(b,c)]
ms = [m for m,a,b,c,*_ in R if not spec(b,c)]
sc = ax.scatter(xs, ys, c=ms, cmap='Blues', s=9, vmin=0, vmax=160, edgecolors='none')
xx = np.linspace(1, 2, 50)
ax.axvline(2, color=INK2, lw=0.8, ls=':')
ax.text(1.04, 112, r'$b<2c$', fontsize=8, color=INK)
ax.text(2.1, 112, r'$b>2c$', fontsize=8, color=INK)
ax.set_xscale('log'); ax.set_xlabel(r'ratio $b/c$ (log scale)'); ax.set_ylabel('Conta-XOR $-$ $(3m-c-3)$')
cb = fig.colorbar(sc, ax=ax, pad=0.01); cb.set_label('$m$', fontsize=8); cb.outline.set_visible(False)
ax.set_ylim(-4, 120)
fig.tight_layout(); fig.savefig(PAPER / 'fig_gain.pdf'); plt.close(fig)
# ---- Fig B: census per degree (degrees without irreducible trinomials)
J = json.load(open(DATA / 'census.json')); F2 = {int(k): v for k, v in J['F2'].items()}; F1 = {int(k): v for k, v in J['F1'].items()}; T = set(J['T'])
fig, ax = plt.subplots(figsize=(6.2, 2.7))
m1 = [m for m in sorted(F1) if m not in T]; m2 = [m for m in sorted(F2) if m not in T]
ax.scatter(m1, [F1[m][0]/m for m in m1], s=7, color=ORANGE, label='first family (BCP), best member', zorder=2)
ax.scatter(m2, [F2[m][0]/m for m in m2], s=7, color=BLUE, label='second family, best member (Thm. 3)', zorder=3)
ax.axhline(8/3, color=INK2, lw=0.8, ls='--'); ax.text(1105, 8/3, r'$8/3$', va='center', fontsize=8)
ax.axhline(3, color=INK2, lw=0.8, ls=':'); ax.text(1105, 3, r'$3$', va='center', fontsize=8)
ax.set_xlabel('degree $m$ (only degrees without an irreducible trinomial)'); ax.set_ylabel('XORs per bit')
ax.set_ylim(2.3, 3.1); ax.set_xlim(0, 1100)
ax.legend(frameon=False, fontsize=7.5, loc='lower right')
fig.tight_layout(); fig.savefig(PAPER / 'fig_census.pdf'); plt.close(fig)
print('ok')
