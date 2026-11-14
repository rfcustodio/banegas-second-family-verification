# Area/depth comparison through degree 1100

This is a **new, isolated experiment**. It does not modify the published paper,
existing datasets, existing figure generators, or verification scripts.

## Run

From the repository root:

```bash
python3 experiments/area_depth_1100.py
```

Requires Python 3 and matplotlib for PDF plots. The CSV is generated even if
matplotlib is not installed.

Generated (ignored by default only if you configure your local .gitignore):
- `experiments/results/best_by_method.csv`
- `experiments/results/metadata.json`
- `experiments/results/xor_per_bit.pdf`
- `experiments/results/xor_depth.pdf`

The script reads the original `data/fam1_irr.txt` and `data/fam2_irr.txt`
without changing them. For each degree and method it chooses the minimum-XOR
irreducible member. The second-family closed-form and chain depths are obtained
from the actual generated straight-line programs, not from theoretical bounds.

**Important limitations:** The first-family BCP construction and the
SAT-optimal special strip programs do not yet expose equivalent executable
SLPs in this experiment. Their gate counts are included, but their depths
are deliberately blank, rather than estimated or replaced by another
construction's depth. The depth plot is therefore **partial**.

The next phase is to extract or implement the exact SAT-optimal strip SLPs
and a BCP first-family SLP, validate their output linear forms, and add
depth values. A full area-depth Pareto analysis will then enumerate all
irreducible members, not only the minimum-XOR member of each method.

No claim of circuit optimality beyond the original SAT-proven small
instances is implied by this experiment.
