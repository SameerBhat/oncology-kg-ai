#!/usr/bin/env python3
"""Inter-annotator agreement metrics for qrels annotations."""
from __future__ import annotations

import argparse
import logging
import os
from itertools import combinations
from typing import Dict, Iterable, Tuple

import numpy as np
import pandas as pd
from sklearn.metrics import cohen_kappa_score

from src.database import MongoDBClient
from src.embedding_utils import setup_logging
from src.config.settings import MONGO_URI as DEFAULT_MONGO_URI

REQUIRED_FIELDS = {"question_id", "node_id", "relevance", "created_by"}


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Compute Cohen's kappa and Krippendorff's alpha for qrels annotations."
    )
    parser.add_argument(
        "--mongo-uri",
        default=os.getenv("MONGO_URI", DEFAULT_MONGO_URI),
        help="MongoDB connection string (default: env MONGO_URI or repo default)",
    )
    parser.add_argument(
        "--database",
        default=os.getenv("QRELS_DB", os.getenv("DB", "oncopro")),
        help="Database name containing the qrels collection (default: env QRELS_DB/DB or 'oncopro')",
    )
    parser.add_argument(
        "--collection",
        default=os.getenv("QRELS_COLLECTION", "qrels"),
        help="Collection name with annotated qrels (default: 'qrels')",
    )
    parser.add_argument(
        "--qrels-version",
        default=os.getenv("QRELS_VERSION"),
        help="Optional qrels_version filter",
    )
    parser.add_argument(
        "--annotators",
        nargs="*",
        default=None,
        help="Optional list of annotator ids (created_by) to include",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug logging",
    )
    return parser.parse_args()


def load_annotations(
    client: MongoDBClient,
    collection_name: str,
    qrels_version: str | None,
    annotators: Iterable[str] | None,
) -> pd.DataFrame:
    """Fetch qrels annotations as a DataFrame."""
    collection = client.get_collection(collection_name)
    query: Dict[str, object] = {}
    if qrels_version:
        query["qrels_version"] = qrels_version
    projection = {"_id": 0, "question_id": 1, "node_id": 1, "relevance": 1, "created_by": 1}
    cursor = collection.find(query, projection)
    df = pd.DataFrame(list(cursor))

    if df.empty:
        return df

    missing = REQUIRED_FIELDS - set(df.columns)
    if missing:
        raise ValueError(f"Missing required fields in qrels documents: {missing}")

    df = df.dropna(subset=["created_by"])

    if annotators:
        annotators_set = {str(a) for a in annotators}
        df = df[df["created_by"].astype(str).isin(annotators_set)]

    # Normalize identifiers to string for consistent pivoting
    df["question_id"] = df["question_id"].astype(str)
    df["node_id"] = df["node_id"].astype(str)
    df["created_by"] = df["created_by"].astype(str)

    df = df.drop_duplicates(["question_id", "node_id", "created_by"], keep="last")
    return df


def build_annotation_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """Return pivot table indexed by (question_id, node_id) with annotators as columns."""
    if df.empty:
        return pd.DataFrame()

    pivot = df.pivot_table(
        index=["question_id", "node_id"],
        columns="created_by",
        values="relevance",
        aggfunc="first",
    )
    pivot = pivot.sort_index()
    return pivot


def compute_pairwise_kappa(matrix: pd.DataFrame) -> Dict[Tuple[str, str], float]:
    """Compute Cohen's kappa for each annotator pair using overlapping items."""
    if matrix.shape[1] < 2:
        return {}

    results: Dict[Tuple[str, str], float] = {}
    for left, right in combinations(matrix.columns, 2):
        subset = matrix[[left, right]].dropna()
        if subset.empty:
            continue
        kappa = cohen_kappa_score(subset[left], subset[right])
        results[(str(left), str(right))] = float(kappa)
    return results


def krippendorffs_alpha_nominal(data: np.ndarray) -> float:
    """Krippendorff's alpha for nominal data with missing values as NaN."""
    if data.size == 0:
        return float("nan")

    mask = ~np.isnan(data)
    if mask.sum() == 0:
        return float("nan")

    valid_values = data[mask]
    categories = np.unique(valid_values)
    if categories.size <= 1:
        return 1.0

    counts_overall = {cat: 0.0 for cat in categories}
    Do_num = 0.0
    Do_den = 0.0

    for unit_idx in range(data.shape[1]):
        unit_mask = mask[:, unit_idx]
        unit_vals = data[:, unit_idx][unit_mask]
        if unit_vals.size == 0:
            continue
        unique_vals, counts = np.unique(unit_vals, return_counts=True)
        n_u = float(unit_vals.size)
        for cat, count in zip(unique_vals, counts):
            counts_overall[cat] += float(count)
            if n_u > 1:
                Do_num += float(count) * (n_u - float(count))
        if n_u > 1:
            Do_den += n_u * (n_u - 1.0)

    if Do_den == 0.0:
        return float("nan")

    Do = Do_num / Do_den
    total_annotations = sum(counts_overall.values())
    if total_annotations <= 1:
        return float("nan")

    De_num = 0.0
    for count in counts_overall.values():
        De_num += count * (total_annotations - count)
    De = De_num / (total_annotations * (total_annotations - 1.0))
    if De == 0.0:
        return 1.0

    return 1.0 - (Do / De)


def main() -> None:
    args = parse_args()
    setup_logging(logging.DEBUG if args.verbose else logging.INFO)

    logging.info("Connecting to MongoDB %s / %s", args.mongo_uri, args.database)
    with MongoDBClient(uri=args.mongo_uri, database_name=args.database) as client:
        df = load_annotations(client, args.collection, args.qrels_version, args.annotators)

    if df.empty:
        logging.warning("No qrels annotations found for the specified parameters.")
        return

    logging.info(
        "Loaded %d qrels rows across %d annotators and %d (question,node) pairs.",
        len(df),
        df["created_by"].nunique(),
        df.drop_duplicates(["question_id", "node_id"]).shape[0],
    )

    matrix = build_annotation_matrix(df)
    if matrix.empty or matrix.shape[1] < 2:
        logging.error("Need at least two annotators with overlapping labels to compute agreement.")
        return

    pairwise = compute_pairwise_kappa(matrix)
    if not pairwise:
        logging.error("No overlapping annotations between annotator pairs; cannot compute Cohen's kappa.")
    else:
        print("\nCohen's κ (pairwise):")
        for (left, right), value in sorted(pairwise.items()):
            print(f"  {left} vs {right}: {value:.3f}")

    alpha = krippendorffs_alpha_nominal(matrix.T.to_numpy(dtype=float))
    if np.isnan(alpha):
        logging.error("Could not compute Krippendorff's alpha (insufficient data).")
    else:
        print(f"\nKrippendorff's α (nominal): {alpha:.3f}")


if __name__ == "__main__":
    main()
