#!/usr/bin/env python3
"""
Render model summary tables (Markdown + LaTeX) from metrics_out/model_summary.csv.
Outputs:
  tables/model_table.md
  tables/model_table.tex
"""
import os, re
import pandas as pd

INDIR = "metrics_out"
OUTDIR = "tables"
os.makedirs(OUTDIR, exist_ok=True)
df = pd.read_csv(os.path.join(INDIR, "model_summary.csv"))

# Pick a tidy set of columns for the paper
wanted = ["P@5", "P@10", "Recall@10", "NDCG@5", "NDCG@10", "MRR", "MAP"]

def format_ci(row, key):
    m = row[f"{key}_mean"]
    lo = row[f"{key}_ci_low"]
    hi = row[f"{key}_ci_high"]
    return f"{m:.3f} [{lo:.3f}–{hi:.3f}]"

rows = []
for _, r in df.iterrows():
    row = {"Model": r["model"], "#Q": int(r["n_queries"])}
    for k in wanted:
        row[k] = format_ci(r, k)
    rows.append(row)

md = "| Model | #Q | " + " | ".join(wanted) + " |\n"
md += "|" + " --- |" * (2 + len(wanted)) + "\n"
for r in rows:
    md += f"| {r['Model']} | {r['#Q']} | " + " | ".join(r[k] for k in wanted) + " |\n"

with open(os.path.join(OUTDIR, "model_table.md"), "w") as f:
    f.write(md)

# LaTeX
def latex_escape(s): return s.replace("_", "\\_")
latex = "\\begin{tabular}{l" + "r"*(1+len(wanted)) + "}\n\\toprule\n"
latex += "Model & \\#Q & " + " & ".join(wanted) + " \\\\\n\\midrule\n"
for r in rows:
    latex += latex_escape(r["Model"]) + f" & {r['#Q']} & " + " & ".join(r[k] for k in wanted) + " \\\\\n"
latex += "\\bottomrule\n\\end{tabular}\n"

with open(os.path.join(OUTDIR, "model_table.tex"), "w") as f:
    f.write(latex)

print("[OK] Wrote tables/model_table.md and .tex")
