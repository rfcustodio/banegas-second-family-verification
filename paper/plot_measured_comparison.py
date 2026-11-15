#!/usr/bin/env python3
"""Produce vector comparison figures from CI artifact area-depth-1100."""
import argparse
from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--data", type=Path, required=True, help="Unpacked CI artifact directory")
    p.add_argument("--out", type=Path, required=True, help="Output figure directory")
    a = p.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    s = pd.read_csv(a.data / "cross_family_measured_summary.csv").sort_values("m")
    assert len(s) == 405
    assert (s.f2_best_gates < s.f1_best_gates).all()
    assert (s.f1_best_depth < s.f2_best_depth).sum() == 404
    plt.rcParams.update({"font.size": 10, "pdf.fonttype": 42})

    fig, ax = plt.subplots(figsize=(7.4, 4.4))
    ax.plot(s.m, s.f1_best_gates, ".", ms=2.4, label="First family: verified SLPs")
    ax.plot(s.m, s.f2_best_gates, ".", ms=2.4, label="Second family: verified SLPs")
    ax.set(xlabel="Field degree m", ylabel="Minimum observed XOR gates",
           title="Measured reduction area, shared irreducible degrees")
    ax.legend(); ax.grid(alpha=.2); fig.tight_layout()
    fig.savefig(a.out / "fig_measured_area.pdf"); plt.close(fig)

    fig, ax = plt.subplots(figsize=(7.4, 4.4))
    ax.scatter(s.m, s.f1_best_depth, s=8, label="First family")
    ax.scatter(s.m, s.f2_best_depth, s=8, alpha=.7, label="Second family")
    ax.set_yscale("log")
    ax.set(xlabel="Field degree m", ylabel="Minimum observed XOR depth (log scale)",
           title="Measured reduction depth, shared irreducible degrees")
    ax.legend(); ax.grid(alpha=.2); fig.tight_layout()
    fig.savefig(a.out / "fig_measured_depth.pdf"); plt.close(fig)

    fig, ax = plt.subplots(figsize=(7.4, 4.4))
    ax.scatter(s.m, s.f2_area_saving_percent, s=10)
    avg = s.f2_area_saving_percent.mean()
    ax.axhline(avg, ls="--", label=f"Mean {avg:.2f}%")
    ax.set(xlabel="Field degree m", ylabel="Area saving of second family (%)",
           title="Relative area saving across 405 shared degrees")
    ax.legend(); ax.grid(alpha=.2); fig.tight_layout()
    fig.savefig(a.out / "fig_measured_saving.pdf"); plt.close(fig)

if __name__ == "__main__":
    main()
