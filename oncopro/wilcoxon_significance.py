# wilcoxon_significance.py
import csv
from scipy.stats import wilcoxon

path = "metrics_out/per_query_ndcg10.csv"
with open(path) as f:
    rows = list(csv.DictReader(f))

models = [c for c in rows[0].keys() if c != "question_id"]

if len(models) < 2:
    print(f"Found only {len(models)} model(s): {models}")
    print("Need at least 2 models to perform significance testing.")
    exit(0)

def extract(model):
    vals = []
    for r in rows:
        v = r.get(model)
        if v in (None, ""): continue
        vals.append(float(v))
    return vals

for i in range(len(models)):
    for j in range(i+1, len(models)):
        a, b = models[i], models[j]
        xa, xb = extract(a), extract(b)
        n = min(len(xa), len(xb))
        x1, x2 = xa[:n], xb[:n]
        stat, p = wilcoxon(x1, x2, zero_method='wilcox', alternative='two-sided')
        print(f"{a} vs {b}: p={p:.4g} (n={n})")
