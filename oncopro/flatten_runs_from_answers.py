#!/usr/bin/env python3
import os
from typing import Any
from pymongo import MongoClient

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DB = os.getenv("DB", "oncopro")
DROP_DUPLICATES = os.getenv("DROP_DUPLICATES", "1") != "0"  # default: drop

client = MongoClient(MONGO_URI)
db = client[DB]
answers = db["answers"]
runs = db["runs"]

runs.drop()
# keep a simple index; use unique key on (question_id, model_name, node_id) to avoid dup rows
runs.create_index([("question_id", 1), ("model_name", 1), ("node_id", 1)], unique=True)

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
                if "id" in n:  return str(n["id"])
                if "_id" in n: return str(n["_id"])
        if "id" in x:  return str(x["id"])
        if "_id" in x: return str(x["_id"])
        if "node_id" in x: return str(x["node_id"])
    return None

def is_marked_duplicate(x: Any) -> bool:
    if not isinstance(x, dict):
        return False
    if x.get("isDuplicate") is True:
        return True
    n = x.get("node")
    if isinstance(n, dict) and n.get("isDuplicate") is True:
        return True
    return False

inserted = answers_seen = 0
skipped_dup_flag = skipped_repeat_id = 0

for a in answers.find({}):
    answers_seen += 1
    qid = str(a.get("question_id") or a.get("question") or a.get("id") or a.get("_id"))
    model = a.get("model_name") or "unknown"
    items = a.get("ordered_nodes") or a.get("nodes") or []

    seen_ids = set()
    rank = 1

    for elem in items:
        if DROP_DUPLICATES and is_marked_duplicate(elem):
            skipped_dup_flag += 1
            continue

        nid = get_node_id(elem)
        if not nid:
            continue

        if DROP_DUPLICATES and nid in seen_ids:
            skipped_repeat_id += 1
            continue

        score = None
        original_index = None
        if isinstance(elem, dict):
            # score may be at top level (SavedNode) or nested under `node`
            try:
                if "score" in elem:
                    score = float(elem.get("score"))
                elif "node" in elem and isinstance(elem["node"], dict) and "score" in elem["node"]:
                    score = float(elem["node"].get("score"))
            except Exception:
                score = None
            if "original_index" in elem:
                try:
                    original_index = int(elem.get("original_index"))
                except Exception:
                    original_index = None

        try:
            runs.insert_one({
                "question_id": qid,
                "model_name": model,
                "node_id": nid,
                "rank": rank,              # rank over kept (unique) nodes
                "score": score,
                "original_index": original_index,
            })
            inserted += 1
            rank += 1
            seen_ids.add(nid)
        except Exception as e:
            # unique index will skip exact duplicates; log and continue
            # print(f"skip insert for ({qid},{model},{nid}): {e}")
            continue

print(
    f"runs built: {inserted} rows from {answers_seen} answers | "
    f"skipped_dup_flag={skipped_dup_flag}, skipped_repeat_id={skipped_repeat_id}, "
    f"DROP_DUPLICATES={'on' if DROP_DUPLICATES else 'off'}"
)
