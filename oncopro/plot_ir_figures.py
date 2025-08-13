#!/usr/bin/env python3
"""
Make paper-ready figures from metrics_out/*.
- NDCG@k curves (mean ± 95% CI) for each model.
- Latency vs NDCG@10 scatter (needs metrics_out/efficiency.csv if available).

Inputs:
  metrics_out/model_summary.csv
  metrics_out/efficiency.csv   (optional; columns: model, median_latency_ms, index_size_mb, build_time_s)

Outputs:
  figures/ndcg_curves.png|svg
  figures/latency_vs_ndcg10.png|svg   (only if efficiency.csv exists)
"""
import os, csv, re
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

OUTDIR_FIG = "figures"
INDIR = "metrics_out"
os.makedirs(OUTDIR_FIG, exist_ok=True)

summary = pd.read_csv(os.path.join(INDIR, "model_summary.csv"))

# ---- Figure 1: NDCG@k curves ----
# infer available ks from columns like "NDCG@5_mean"
ndcg_cols = [c for c in summary.columns if re.match(r"NDCG@\d+_mean$", c)]
ks = sorted(int(re.findall(r"\d+", c)[0]) for c in ndcg_cols)

plt.figure()
for _, row in summary.iterrows():
    model = row["model"]
    means = [row[f"NDCG@{k}_mean"] for k in ks]
    lows  = [row[f"NDCG@{k}_ci_low"] for k in ks]
    highs = [row[f"NDCG@{k}_ci_high"] for k in ks]
    yerr = np.array([np.array(means) - np.array(lows), np.array(highs) - np.array(means)])
    plt.errorbar(ks, means, yerr=yerr, capsize=3, marker='o', label=model)

plt.xlabel("k")
plt.ylabel("NDCG@k")
plt.title("NDCG@k (mean ± 95% CI)")
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(OUTDIR_FIG, "ndcg_curves.png"), dpi=200)
plt.savefig(os.path.join(OUTDIR_FIG, "ndcg_curves.svg"))

# ---- Figure 2: Latency vs NDCG@10 (optional) ----
eff_path = os.path.join(INDIR, "efficiency.csv")
if os.path.exists(eff_path):
    eff = pd.read_csv(eff_path)
    # join NDCG@10 mean
    ndcg10 = summary[["model", "NDCG@10_mean"]]
    df = eff.merge(ndcg10, on="model", how="inner")

    plt.figure()
    x = df["median_latency_ms"].values
    y = df["NDCG@10_mean"].values
    sizes = (df.get("index_size_mb", pd.Series([50]*len(df))) * 2).values  # scale bubbles
    for i, r in df.iterrows():
        plt.scatter(r["median_latency_ms"], r["NDCG@10_mean"], s=sizes[i])
        plt.text(r["median_latency_ms"], r["NDCG@10_mean"], r["model"], fontsize=8, ha="left", va="bottom")
    plt.xlabel("Median query latency (ms)")
    plt.ylabel("NDCG@10")
    plt.title("Latency vs NDCG@10 (bubble size ∝ index size MB)")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTDIR_FIG, "latency_vs_ndcg10.png"), dpi=200)
    plt.savefig(os.path.join(OUTDIR_FIG, "latency_vs_ndcg10.svg"))
else:
    print("[INFO] metrics_out/efficiency.csv not found; skipping latency figure.")
