#!/usr/bin/env python3
"""
Wilcoxon signed-rank tests on per-query NDCG@10.
Inputs:
  metrics_out/per_query_ndcg10.csv  (from compute_metrics.py)
Outputs:
  tables/wilcoxon_ndcg10.csv
  tables/wilcoxon_ndcg10.md
"""
import os, csv, itertools
import numpy as np
from scipy.stats import wilcoxon

INDIR = "metrics_out"
OUTDIR = "tables"
os.makedirs(OUTDIR, exist_ok=True)

rows = list(csv.DictReader(open(os.path.join(INDIR, "per_query_ndcg10.csv"))))
models = [c for c in rows[0].keys() if c != "question_id"]

def vec(model):
    vals = []
    for r in rows:
        v = r.get(model, "")
        if v == "": continue
        vals.append(float(v))
    return np.array(vals)

# Matrix compute
P = { (a,b): None for a,b in itertools.permutations(models, 2) }
for i,a in enumerate(models):
    xa = vec(a)
    for j,b in enumerate(models):
        if i >= j: continue
        xb = vec(b)
        n = min(len(xa), len(xb))
        if n == 0:
            p = float("nan")
        else:
            stat, p = wilcoxon(xa[:n], xb[:n], zero_method='wilcox', alternative='two-sided')
        P[(a,b)] = p
        P[(b,a)] = p

# CSV
csv_path = os.path.join(OUTDIR, "wilcoxon_ndcg10.csv")
with open(csv_path, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["model"] + models)
    for a in models:
        row = [a] + [ ("" if a==b else (f"{P[(a,b)]:.4g}" if P[(a,b)] is not None else "")) for b in models ]
        w.writerow(row)

# Markdown
md_path = os.path.join(OUTDIR, "wilcoxon_ndcg10.md")
with open(md_path, "w") as f:
    f.write("| model | " + " | ".join(models) + " |\n")
    f.write("|" + " --- |"*(1+len(models)) + "\n")
    for a in models:
        cells = []
        for b in models:
            if a == b: cells.append("—")
            else:
                p = P[(a,b)]
                cells.append("" if p is None else f"{p:.4g}")
        f.write(f"| {a} | " + " | ".join(cells) + " |\n")

print(f"[OK] wrote {csv_path} and {md_path}")
