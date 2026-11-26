import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

# f_{6,3}(x) = G(x^3), G = f_{2,1}, so gamma = 3 and m = 12.
gamma, m = 3, 12
f_exps = [12, 9, 6, 3, 0]            # exponents of f = x^12+x^9+x^6+x^3+1
N = 2 * m - 1                         # input coefficients d_0 .. d_{2m-2}
colors = ["#1f77b4", "#ff7f0e", "#2ca02c"]

fig, ax = plt.subplots(figsize=(7.2, 2.6))
for j in range(N):
    r = j % gamma
    ax.add_patch(Rectangle((j, 1.0), 0.92, 0.9, facecolor=colors[r], alpha=0.35, edgecolor="black", lw=0.6))
    ax.text(j + 0.46, 1.45, str(j), ha="center", va="center", fontsize=7)
for r in range(gamma):
    ax.text(-0.9, 1.45 + 0.0, "", ha="center")
# marks under the exponents of f
for e in f_exps:
    ax.add_patch(Rectangle((e, 0.25), 0.92, 0.45, facecolor="none", edgecolor="black", lw=1.2, hatch="////"))
ax.text(-0.6, 0.47, "exponents\nof $f$", ha="right", va="center", fontsize=7)
ax.text(-0.6, 1.45, "$d_j$", ha="right", va="center", fontsize=8)
# strip labels
for r in range(gamma):
    xs = [j for j in range(N) if j % gamma == r]
    ax.plot([min(xs), max(xs) + 0.92], [2.15 + 0.12 * r, 2.15 + 0.12 * r], color=colors[r], lw=2)
    ax.text(max(xs) + 1.0, 2.15 + 0.12 * r, f"strip {r}", va="center", fontsize=7, color=colors[r])
ax.set_xlim(-4.2, N + 3.2)
ax.set_ylim(0.0, 2.8)
ax.axis("off")
plt.tight_layout()
plt.savefig("fig_strips.pdf")
print("ok")
