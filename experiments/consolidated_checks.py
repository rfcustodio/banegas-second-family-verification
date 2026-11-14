#!/usr/bin/env python3
"""Cross-check the complete experimental results without mixing area and depth models."""
import csv
import json
from pathlib import Path
OUT=Path(__file__).resolve().parent/"results"
def load(name):
    with (OUT/name).open(newline="") as f:return list(csv.DictReader(f))
def main():
    comp=load("f1_f2_formula_comparison.csv")
    f2=load("f2_area_depth_summary.csv")
    special=load("special_frontier_effect.csv")
    baseline=load("f1_contaxor_baseline.csv")
    allslps=load("all_f2_slps.csv")
    assert len(comp)==405 and len(f2)==720 and len(special)==15
    assert len(allslps)==3016
    assert all(int(r["f2_minus_f1"])==int(r["f2_formula_xors"])-int(r["f1_formula_xors"]) for r in comp)
    assert all(int(r["f2_minus_f1"])<0 for r in comp)
    assert all(int(r["gates"])==int(r["bcp_formula"]) for r in baseline)
    assert sum(r["strip_on_frontier"]=="True" for r in special)==14
    assert sum(int(r["new_min_gates"])<int(r["old_min_gates"]) for r in special)==14
    assert sum(int(r["new_min_depth"])<int(r["old_min_depth"]) for r in special)==13
    assert sum(int(r["pareto_points"])>1 for r in f2)==383
    mean=sum((int(r["f1_formula_xors"])-int(r["f2_formula_xors"]))/int(r["f1_formula_xors"]) for r in comp)/len(comp)
    summary={"shared_degrees":len(comp),"f2_area_better_degrees":len(comp),
             "mean_relative_f2_area_saving_pct":round(100*mean,5),
             "f2_irreducible_members":len(allslps)//2,
             "f2_generated_slps":len(allslps),
             "f2_degrees_with_area_depth_tradeoff":383,
             "special_heuristic_improve_area":14,
             "special_heuristic_improve_depth":13,
             "first_family_heuristic_slps_tested":len(baseline),
             "important":"F1 formula vs F2 formula area; F1 Conta-XOR depth is not BCP depth"}
    (OUT/"consolidated_checks.json").write_text(json.dumps(summary,indent=2)+"\n")
    print(json.dumps(summary,indent=2))
if __name__=="__main__":main()
