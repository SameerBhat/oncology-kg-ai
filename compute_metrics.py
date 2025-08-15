#!/usr/bin/env python3
"""
Compute IR metrics from MongoDB `qrels` and `runs`.

Outputs:
  - metrics_out/model_summary.csv        (means + 95% CIs per model)
  - metrics_out/per_query_metrics.csv    (one row per model×question)
  - metrics_out/per_query_ndcg10.csv     (wide table: question_id + NDCG@10 per model)

Assumptions:
  - qrels collection: {question_id, node_id, relevance, qrels_version, ...}
  - runs  collection: {question_id, model_name, node_id, rank, score?, original_index?}
  - Relevance is graded (0..N). "Relevant" for P/R/MAP/MRR means rel >= positive_min.
  - Queries with TOTAL relevant == 0 in qrels are excluded from averages (standard IR practice).

Usage examples:
  python compute_metrics.py
  python compute_metrics.py --qrels-version v1 --k 1 3 5 10 20 --bootstrap 2000
  python compute_metrics.py --model-include "jina|Qwen" --outdir results_ir

Requires:
  pip install pymongo numpy
"""

import os
import re
import csv
import math
import argparse
from collections import defaultdict
from typing import Dict, List, Tuple
import numpy as np
from pymongo import MongoClient


def parse_args():
    p = argparse.ArgumentParser(description="Compute IR metrics from qrels and runs")
    p.add_argument("--mongo-uri", default=os.getenv("MONGO_URI", "mongodb://localhost:27017/"))
    p.add_argument("--db", default=os.getenv("DB", "oncopro"))
    p.add_argument("--qrels-version", default=os.getenv("QRELS_VERSION", "v1"))
    p.add_argument("--k", nargs="+", type=int, default=[1, 3, 5, 10],
                   help="Cutoffs for @k metrics")
    p.add_argument("--positive-min", type=int, default=1,
                   help="Relevance >= positive_min counts as 'relevant' for P/R/MAP/MRR (default: 1)")
    p.add_argument("--bootstrap", type=int, default=1000,
                   help="Bootstrap resamples for 95%% CI (0 = use normal approx)")
    p.add_argument("--model-include", type=str, default=None,
                   help="Regex; only include models whose name matches")
    p.add_argument("--model-exclude", type=str, default=None,
                   help="Regex; exclude models whose name matches")
    p.add_argument("--outdir", type=str, default="metrics_out")
    return p.parse_args()


# -------------------- Metric helpers --------------------

def dcg_at_k(rels: List[int], k: int) -> float:
    # Graded DCG (2^rel - 1) / log2(rank+1)
    upto = min(k, len(rels))
    return sum(((2 ** rels[i] - 1) / math.log2(i + 2)) for i in range(upto))


def ndcg_at_k(rels: List[int], k: int) -> float:
    if not rels:
        return 0.0
    ideal = sorted(rels, reverse=True)
    idcg = dcg_at_k(ideal, k)
    if idcg == 0:
        return 0.0
    return dcg_at_k(rels, k) / idcg


def precision_at_k(rels: List[int], k: int, pos_min: int) -> float:
    hits = sum(1 for r in rels[:k] if r >= pos_min)
    return hits / float(k)


def recall_at_k(rels: List[int], k: int, total_rel: int, pos_min: int) -> float:
    hits = sum(1 for r in rels[:k] if r >= pos_min)
    return (hits / float(total_rel)) if total_rel > 0 else 0.0


def mrr(rels: List[int], pos_min: int) -> float:
    for i, r in enumerate(rels, start=1):
        if r >= pos_min:
            return 1.0 / i
    return 0.0


def average_precision(rels: List[int], pos_min: int) -> float:
    num_rel = sum(1 for r in rels if r >= pos_min)
    if num_rel == 0:
        return 0.0
    hits = 0
    ap = 0.0
    for i, r in enumerate(rels, start=1):
        if r >= pos_min:
            hits += 1
            ap += hits / float(i)
    return ap / float(num_rel)


# -------------------- Data loading --------------------

def load_qrels(db, qrels_version: str) -> Dict[str, Dict[str, int]]:
    """Return dict: question_id -> {node_id: relevance}"""
    qrels_by_q: Dict[str, Dict[str, int]] = defaultdict(dict)
    cur = db["qrels"].find({"qrels_version": qrels_version})
    count = 0
    for r in cur:
        qid = str(r["question_id"])
        nid = str(r["node_id"])
        rel = int(r.get("relevance", 0))
        qrels_by_q[qid][nid] = rel
        count += 1
    if count == 0:
        print(f"[WARN] No qrels found for version '{qrels_version}'.")
    else:
        print(f"[INFO] Loaded {count} qrels rows across {len(qrels_by_q)} questions.")
    return qrels_by_q


def load_runs(db,
              model_include: str = None,
              model_exclude: str = None) -> Dict[str, Dict[str, List[Tuple[int, str]]]]:
    """
    Return dict: model_name -> question_id -> list of (rank, node_id) sorted by rank.
    De-duplicates node_id within each (model, question), keeping the earliest rank.
    """
    inc_re = re.compile(model_include) if model_include else None
    exc_re = re.compile(model_exclude) if model_exclude else None

    runs_by_mq: Dict[str, Dict[str, List[Tuple[int, str]]]] = defaultdict(lambda: defaultdict(list))

    cur = db["runs"].aggregate([
        {"$sort": {"model_name": 1, "question_id": 1, "rank": 1}}
    ])

    total_rows = 0
    kept_rows = 0
    for row in cur:
        total_rows += 1
        model = row.get("model_name") or "unknown"
        if inc_re and not inc_re.search(model):
            continue
        if exc_re and exc_re.search(model):
            continue

        qid = str(row["question_id"])
        nid = str(row["node_id"])
        rank = int(row.get("rank", 10**9))

        # de-duplicate by node_id within (model, question)
        existing = runs_by_mq[model][qid]
        if any(nid == n for _, n in existing):
            continue

        runs_by_mq[model][qid].append((rank, nid))
        kept_rows += 1

    # Ensure lists are sorted by rank
    for model, qmap in runs_by_mq.items():
        for qid in qmap:
            qmap[qid].sort(key=lambda x: x[0])

    print(f"[INFO] Loaded runs: {total_rows} rows -> {kept_rows} kept after de-dup.")
    print(f"[INFO] Models found: {len(runs_by_mq)}")
    return runs_by_mq


# -------------------- Evaluation --------------------

def evaluate_per_query(ranked_node_ids: List[str],
                       qrels_lookup: Dict[str, int],
                       k_list: List[int],
                       pos_min: int) -> Dict[str, float]:
    """
    ranked_node_ids: node ids in rank order (unique per question)
    qrels_lookup: node_id -> relevance
    """
    rels = [int(qrels_lookup.get(nid, 0)) for nid in ranked_node_ids]
    total_rel = sum(1 for v in qrels_lookup.values() if v >= pos_min)

    # If this query has no relevant documents in qrels, we skip it in aggregation
    if total_rel == 0:
        return {"_skip": 1}

    out = {}
    for k in k_list:
        out[f"P@{k}"] = precision_at_k(rels, k, pos_min)
        out[f"Recall@{k}"] = recall_at_k(rels, k, total_rel, pos_min)
        out[f"NDCG@{k}"] = ndcg_at_k(rels, k)
    out["MRR"] = mrr(rels, pos_min)
    out["MAP"] = average_precision(rels, pos_min)
    out["_skip"] = 0
    return out


def aggregate_with_ci(per_query_rows: List[Dict[str, float]],
                      metrics_keys: List[str],
                      bootstrap: int = 1000) -> Tuple[Dict[str, float], Dict[str, Tuple[float, float]]]:
    """
    Returns: (means, cis) where
      means[k] = mean score
      cis[k]   = (low95, high95)
    """
    if not per_query_rows:
        return {}, {}

    # Build matrix: rows = queries, cols = metrics
    mat = {k: np.array([row[k] for row in per_query_rows]) for k in metrics_keys}

    means = {k: float(np.mean(mat[k])) for k in metrics_keys}

    if bootstrap and bootstrap > 0:
        # non-parametric bootstrap over queries
        n = len(per_query_rows)
        rng = np.random.default_rng(12345)
        lows, highs = {}, {}
        for k in metrics_keys:
            samples = []
            for _ in range(bootstrap):
                idx = rng.integers(0, n, size=n)
                samples.append(np.mean(mat[k][idx]))
            low = float(np.percentile(samples, 2.5))
            high = float(np.percentile(samples, 97.5))
            lows[k], highs[k] = low, high
        cis = {k: (lows[k], highs[k]) for k in metrics_keys}
        return means, cis
    else:
        # normal approx (t ~ 1.96)
        cis = {}
        for k in metrics_keys:
            arr = mat[k]
            std = float(np.std(arr, ddof=1)) if len(arr) > 1 else 0.0
            ci = 1.96 * std / math.sqrt(max(1, len(arr)))
            cis[k] = (means[k] - ci, means[k] + ci)
        return means, cis


# -------------------- Main --------------------

def main():
    args = parse_args()
    os.makedirs(args.outdir, exist_ok=True)

    client = MongoClient(args.mongo_uri)
    db = client[args.db]

    qrels_by_q = load_qrels(db, args.qrels_version)
    runs_by_mq = load_runs(db, args.model_include, args.model_exclude)

    k_list = sorted(set(args.k))
    metrics_keys = [f"P@{k}" for k in k_list] + \
                   [f"Recall@{k}" for k in k_list] + \
                   [f"NDCG@{k}" for k in k_list] + ["MRR", "MAP"]

    # Per-query table (for export)
    per_query_rows_all_models = []    # dicts: {model, question_id, metrics...}

    # Wide NDCG@10 table (for significance)
    want_ndcg_k = 10
    ndcg10_by_q_model: Dict[str, Dict[str, float]] = defaultdict(dict)

    summary_rows = []  # model-level summary

    for model, q2ranked in runs_by_mq.items():
        per_query_rows = []
        eval_count = 0
        for qid, ranked_pairs in q2ranked.items():
            # Skip queries that lack qrels entirely
            if qid not in qrels_by_q:
                continue

            # rank order over unique node_ids
            ranked_node_ids = [nid for _, nid in sorted(ranked_pairs, key=lambda x: x[0])]

            perq = evaluate_per_query(
                ranked_node_ids=ranked_node_ids,
                qrels_lookup=qrels_by_q[qid],
                k_list=k_list,
                pos_min=args.positive_min,
            )

            if perq.get("_skip", 0) == 1:
                continue  # no relevant in qrels

            eval_count += 1
            # Fill per-query export row
            outrow = {"model": model, "question_id": qid}
            for key in metrics_keys:
                outrow[key] = perq[key]
            per_query_rows.append({k: outrow[k] for k in outrow})
            per_query_rows_all_models.append({k: outrow[k] for k in outrow})

            # NDCG@10 capture
            if f"NDCG@{want_ndcg_k}" in perq:
                ndcg10_by_q_model[qid][model] = perq[f"NDCG@{want_ndcg_k}"]

        if eval_count == 0:
            print(f"[WARN] Model '{model}' has 0 evaluable queries (no labels or zero-relevant). Skipping summary.")
            continue

        means, cis = aggregate_with_ci(per_query_rows, metrics_keys, bootstrap=args.bootstrap)

        # Summarize
        summary = {"model": model, "n_queries": eval_count}
        for key in metrics_keys:
            low, high = cis[key]
            summary[f"{key}_mean"] = means[key]
            summary[f"{key}_ci_low"] = low
            summary[f"{key}_ci_high"] = high
        summary_rows.append(summary)

    if not summary_rows:
        print("[ERROR] No models had evaluable queries. Check qrels version and runs data.")
        return

    # ---- Write CSVs ----
    # 1) Model summary
    summary_path = os.path.join(args.outdir, "model_summary.csv")
    fieldnames = ["model", "n_queries"] + [
        f"{m}_{suf}" for m in metrics_keys for suf in ("mean", "ci_low", "ci_high")
    ]
    with open(summary_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for row in summary_rows:
            w.writerow(row)
    print(f"[OK] Wrote {summary_path}")

    # 2) Per-query metrics (long)
    perq_path = os.path.join(args.outdir, "per_query_metrics.csv")
    perq_fields = ["model", "question_id"] + metrics_keys
    with open(perq_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=perq_fields)
        w.writeheader()
        for row in per_query_rows_all_models:
            w.writerow(row)
    print(f"[OK] Wrote {perq_path}")

    # 3) Wide per-query NDCG@10 (handy for Wilcoxon outside this script)
    ndcg10_path = os.path.join(args.outdir, "per_query_ndcg10.csv")
    # Make a stable list of models present
    all_models = sorted({m for _, md in ndcg10_by_q_model.items() for m in md.keys()})
    with open(ndcg10_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["question_id"] + all_models)
        for qid in sorted(ndcg10_by_q_model.keys()):
            row = [qid] + [ndcg10_by_q_model[qid].get(m, "") for m in all_models]
            w.writerow(row)
    print(f"[OK] Wrote {ndcg10_path}")

    print("[DONE] Metrics computed.")


if __name__ == "__main__":
    main()

# python compute_metrics.py \
#   --qrels-version v1 \
#   --k 1 3 5 10 \
#   --bootstrap 1000 \
#   --outdir metrics_out