#!/usr/bin/env python3
# flatten_runs_from_answers.py
"""
Materialize a `runs` collection from `answers`.
- Uses `ordered_nodes` if present, else fallback to `nodes`.
- Extracts node ids from `id` or `_id` (or nested under `node`).
- Keeps rank as the list order.
ENV:
  MONGO_URI, DB (defaults mongodb://localhost:27017/, oncopro)
"""
import os
from typing import Any
from pymongo import MongoClient

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DB = os.getenv("DB", "oncopro")

client = MongoClient(MONGO_URI)
db = client[DB]
answers = db["answers"]
runs = db["runs"]

runs.drop()
runs.create_index([("question_id", 1), ("model_name", 1), ("rank", 1)])


def get_node_id(x: Any) -> str | None:
    if x is None:
        return None
    if isinstance(x, str):
        return x
    if isinstance(x, dict):
        if "node" in x:
            n = x.get("node")
            if isinstance(n, str):
                return n
            if isinstance(n, dict):
                if "id" in n:
                    return str(n["id"])
                if "_id" in n:
                    return str(n["_id"])
        if "id" in x:
            return str(x["id"])
        if "_id" in x:
            return str(x["_id"])
        if "node_id" in x:
            return str(x["node_id"])
    return None

count = 0
answers_seen = 0
for a in answers.find({}):
    answers_seen += 1
    qid = str(a.get("question_id") or a.get("question") or a.get("id") or a.get("_id"))
    model = a.get("model_name") or "unknown"
    items = a.get("ordered_nodes") or a.get("nodes") or []

    rank = 1
    for elem in items:
        nid = get_node_id(elem)
        if not nid:
            continue
        score = None
        original_index = None
        if isinstance(elem, dict):
            # score may be at top level (legacy SavedNode)
            if "score" in elem:
                try:
                    score = float(elem.get("score"))
                except Exception:
                    score = None
            # or nested under `node`
            if "node" in elem and isinstance(elem["node"], dict) and "score" in elem["node"]:
                try:
                    score = float(elem["node"].get("score"))
                except Exception:
                    pass
            # original_index may be top-level in OrderedNodeRecord
            if "original_index" in elem:
                try:
                    original_index = int(elem.get("original_index"))
                except Exception:
                    original_index = None
        runs.insert_one({
            "question_id": qid,
            "model_name": model,
            "node_id": nid,
            "rank": rank,
            "score": score,
            "original_index": original_index,
        })
        count += 1
        rank += 1

print(f"runs built: {count} rows from {answers_seen} answers")