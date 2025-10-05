import pandas as pd
import numpy as np
from scipy.stats import wilcoxon
import statsmodels.stats.multitest as smm

def generate_wilcoxon_table(csv_file, out_tex="wilcoxon_ndcg10_table.tex"):
    # Load data
    df = pd.read_csv(csv_file)

    # Identify model columns
    model_cols = [c for c in df.columns if c.lower() != "question_id"]
    for c in model_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    # Pairwise Wilcoxon
    pairs = []
    for i in range(len(model_cols)):
        for j in range(i+1, len(model_cols)):
            m1, m2 = model_cols[i], model_cols[j]
            sub = df[[m1, m2]].dropna()
            if len(sub) > 0:
                try:
                    stat, p = wilcoxon(sub[m1], sub[m2])
                except ValueError:
                    p = 1.0  # fallback if all values equal
                pairs.append((m1, m2, p))

    # FDR correction
    pvals = [p for (_, _, p) in pairs]
    reject, qvals, _, _ = smm.multipletests(pvals, alpha=0.05, method="fdr_bh")

    # Build results
    results = []
    for (m1, m2, p), q, sig in zip(pairs, qvals, reject):
        results.append({
            "Model A": m1,
            "Model B": m2,
            "p": p,
            "q": q,
            "Significant at FDR 0.05?": "Yes" if sig else "No"
        })

    df_results = pd.DataFrame(results).sort_values(by=["q", "p"]).reset_index(drop=True)

    # Print to console
    print(df_results.to_string(index=False))

    # Save LaTeX
    def fmt(x): return f"{x:.6f}"
    lines = []
    lines.append("\\begin{table}[t]")
    lines.append("\\centering")
    lines.append("\\footnotesize")
    lines.append("\\caption{Pairwise Wilcoxon signed-rank tests on per-query $\\mathrm{NDCG@10}$ (BH-FDR controlled at $\\alpha=0.05$).}")
    lines.append("\\label{tab:wilcoxon_ndcg10}")
    lines.append("\\begin{tabular}{ccccc}")
    lines.append("\\toprule")
    lines.append("\\textbf{Model A} & \\textbf{Model B} & $\\mathbf{p}$ & $\\mathbf{q}$ & \\textbf{Significant at FDR 0.05?} \\\\")
    lines.append("\\midrule")
    for _, r in df_results.iterrows():
        lines.append(f"{r['Model A']} & {r['Model B']} & {fmt(r['p'])} & {fmt(r['q'])} & {r['Significant at FDR 0.05?']} \\\\")
    lines.append("\\bottomrule")
    lines.append("\\end{tabular}")
    lines.append("\\end{table}")

    with open(out_tex, "w") as f:
        f.write("\n".join(lines))

    print(f"\nLaTeX table saved to {out_tex}")
    return df_results
