# bootstrap_qrels_from_ordered.py
import os, sys, time
from datetime import datetime,timezone
from typing import Any, Dict, List
from pymongo import MongoClient
from bson import ObjectId

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DB = os.getenv("DB", "oncopro")
TOP_R = int(os.getenv("TOP_R", "5"))
QRELS_VERSION = os.getenv("QRELS_VERSION", "v1")
CREATED_BY = os.getenv("CREATED_BY", "bootstrap")

# --- helpers ---------------------------------------------------------------

def get_node_id(x: Any) -> str | None:
    """Extract node_id from various shapes: OrderedNodeRecord, SavedNode, or raw id string."""
    if x is None:
        return None
    if isinstance(x, str):
        return x
    if isinstance(x, dict):
        # OrderedNodeRecord: { node: string|SavedNode, original_index: int }
        if "node" in x:
            n = x["node"]
            if isinstance(n, str):
                return n
            if isinstance(n, dict) and "id" in n:
                return str(n["id"])
        # Maybe it's just a SavedNode embedded
        if "id" in x:
            return str(x["id"])
    return None

# --- main -----------------------------------------------------------------

client = MongoClient(MONGO_URI)
db = client[DB]
answers = db["answers"]
qrels = db["qrels"]

# index for idempotency
qrels.create_index([("question_id", 1), ("node_id", 1), ("qrels_version", 1)], unique=True)

# Build per-question map of node_id -> max relevance seen across models
per_q: Dict[str, Dict[str, int]] = {}

for a in answers.find({"completed": True}):
    qid = str(a.get("question_id") or a.get("question"))
    if not qid:
        continue
    items = a.get("ordered_nodes") or a.get("nodes") or []
    # Normalize to list of node_ids in curated rank order
    ranked_ids: List[str] = []
    for elem in items:
        nid = get_node_id(elem)
        if nid:
            ranked_ids.append(nid)
    # Assign relevance by top-R rule
    rel_map = per_q.setdefault(qid, {})
    for rank, nid in enumerate(ranked_ids, start=1):
        rel = 1 if rank <= TOP_R else 0
        rel_map[nid] = max(rel_map.get(nid, 0), rel)

# Upsert into qrels
now = datetime.now(timezone.utc)
inserted = 0
updated = 0
for qid, rels in per_q.items():
    for nid, rel in rels.items():
        insert_doc = {
            "question_id": qid,
            "node_id": nid,
            "qrels_version": QRELS_VERSION,
            "created_at": now,
            "created_by": CREATED_BY,
        }
        update_doc = {
            "relevance": int(rel),
            "updated_at": now
        }
        try:
            result = qrels.update_one(
                {"question_id": qid, "node_id": nid, "qrels_version": QRELS_VERSION},
                {"$setOnInsert": insert_doc, "$set": update_doc},
                upsert=True,
            )
            if result.upserted_id:
                inserted += 1
            else:
                updated += 1
        except Exception as e:
            print(f"Error upserting qrel for question {qid}, node {nid}: {e}")
            updated += 1

print(f"qrels bootstrap done: upserts={inserted}, updated={updated}, questions={len(per_q)}")