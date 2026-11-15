#!/usr/bin/env python3
"""Plot measured *joint* Pareto fronts from the verified CI artifact.

Run:
  python paper/plot_measured_pareto.py --data /path/to/area-depth-1100 --out paper
"""
import argparse
from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    front = pd.read_csv(args.data / "cross_family_measured_pareto.csv")
    required = {"m", "family", "method", "b", "c", "gates", "depth"}
    assert required.issubset(front.columns)
    degrees = (155, 163, 228, 571)
    fig, axs = plt.subplots(2, 2, figsize=(9, 6.5), constrained_layout=True)
    for ax, m in zip(axs.flat, degrees):
        rows = front.loc[front.m == m]
        assert not rows.empty
        for fam, marker in (("F1", "s"), ("F2", "o")):
            subset = rows.loc[rows.family == fam].sort_values("gates")
            if not subset.empty:
                ax.scatter(subset.gates, subset.depth, marker=marker, s=38,
                           label="First family" if fam == "F1" else "Second family")
        ax.set_title(f"m = {m}")
        ax.set_xlabel("XOR gates")
        ax.set_ylabel("XOR depth")
        ax.grid(alpha=.25)
        ax.legend(fontsize=8)
    fig.savefig(args.out / "fig_joint_pareto_selected.pdf", bbox_inches="tight")
    plt.close(fig)

if __name__ == "__main__":
    main()
