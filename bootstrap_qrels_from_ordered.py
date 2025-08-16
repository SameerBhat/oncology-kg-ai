import os, sys, time
from datetime import datetime, timezone
from typing import Any, Dict, List
from pymongo import MongoClient

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DB = os.getenv("DB", "oncopro")
TOP_R = int(os.getenv("TOP_R", "5"))
QRELS_VERSION = os.getenv("QRELS_VERSION", "v1")
CREATED_BY = os.getenv("CREATED_BY", "bootstrap")

def get_node_id(x: Any) -> str | None:
    """Extract node_id from OrderedNodeRecord, SavedNode, or raw id string."""
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
            if isinstance(n, dict):
                if "id" in n:
                    return str(n["id"])
                if "_id" in n:
                    return str(n["_id"])
        # Embedded SavedNode or legacy
        if "id" in x:
            return str(x["id"])
        if "_id" in x:
            return str(x["_id"])
    return None

def is_marked_duplicate(x: Any) -> bool:
    """True if the element itself or its nested node carries isDuplicate=True."""
    if not isinstance(x, dict):
        return False
    if x.get("isDuplicate") is True:
        return True
    n = x.get("node")
    if isinstance(n, dict) and n.get("isDuplicate") is True:
        return True
    return False

def is_marked_irrelevant(x: Any) -> bool:
    """True if the element itself or its nested node carries isIrrelevant=True."""
    if not isinstance(x, dict):
        return False
    if x.get("isIrrelevant") is True:
        return True
    n = x.get("node")
    if isinstance(n, dict) and n.get("isIrrelevant") is True:
        return True
    return False

client = MongoClient(MONGO_URI)
db = client[DB]
answers = db["answers"]
qrels = db["qrels"]

qrels.create_index([("question_id", 1), ("node_id", 1), ("qrels_version", 1)], unique=True)

# also accept answers that have an ordered list even if completed is false
cursor = answers.find({
    "$or": [
        {"completed": True},
        {"ordered_nodes": {"$exists": True, "$ne": []}}
    ]
})

per_q: Dict[str, Dict[str, int]] = {}
kept_cnt = skipped_dup_flag = skipped_repeat_id = skipped_irrelevant = 0

for a in cursor:
    qid = str(a.get("question_id") or a.get("question") or a.get("_id") or a.get("id"))
    if not qid:
        continue

    items = a.get("ordered_nodes") or a.get("nodes") or []
    seen_ids = set()
    ranked_unique_ids: List[str] = []
    irrelevant_ids: List[str] = []

    for elem in items:
        # skip anything explicitly marked duplicate
        if is_marked_duplicate(elem):
            skipped_dup_flag += 1
            continue
        
        nid = get_node_id(elem)
        if not nid:
            continue
            
        # skip repeats of the same node_id within this answer
        if nid in seen_ids:
            skipped_repeat_id += 1
            continue
            
        seen_ids.add(nid)
        
        # check if marked as irrelevant
        if is_marked_irrelevant(elem):
            irrelevant_ids.append(nid)
            skipped_irrelevant += 1
        else:
            ranked_unique_ids.append(nid)
            kept_cnt += 1

    # Assign relevance: top-R unique items -> 1, rest -> 0, irrelevant -> -1
    rel_map = per_q.setdefault(qid, {})
    for rank, nid in enumerate(ranked_unique_ids, start=1):
        rel = 1 if rank <= TOP_R else 0
        # take the max across multiple models / answers
        rel_map[nid] = max(rel_map.get(nid, 0), rel)
    
    # Mark irrelevant nodes with negative relevance
    for nid in irrelevant_ids:
        # use -1 to indicate irrelevance, but only if not already marked as relevant
        rel_map[nid] = min(rel_map.get(nid, -1), -1)

now = datetime.now(timezone.utc)
inserted = updated = 0
for qid, rels in per_q.items():
    for nid, rel in rels.items():
        insert_doc = {
            "question_id": qid,
            "node_id": nid,
            "qrels_version": QRELS_VERSION,
            "created_at": now,
            "created_by": CREATED_BY,
        }
        update_doc = {"relevance": int(rel), "updated_at": now}
        res = qrels.update_one(
            {"question_id": qid, "node_id": nid, "qrels_version": QRELS_VERSION},
            {"$setOnInsert": insert_doc, "$set": update_doc},
            upsert=True,
        )
        if res.upserted_id: inserted += 1
        else: updated += 1

print(
    f"qrels bootstrap done: upserts={inserted}, updated={updated}, "
    f"questions={len(per_q)}, kept={kept_cnt}, "
    f"skipped_dup_flag={skipped_dup_flag}, skipped_repeat_id={skipped_repeat_id}, "
    f"skipped_irrelevant={skipped_irrelevant}"
)
