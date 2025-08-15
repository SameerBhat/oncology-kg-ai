#!/usr/bin/env python3
"""
Auto-pick success/failure case studies and render markdown pages.

Heuristics:
- Success: a query where some model has NDCG@10 >= 0.9 and the spread (max-min) >= 0.3; else best overall.
- Failure: a query where max NDCG@10 <= 0.2; else the lowest-overall query.

Outputs:
  case_studies/success.md
  case_studies/failure.md
"""
import os, re, math
from typing import Dict, List, Tuple
from pymongo import MongoClient
import pandas as pd

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DB = os.getenv("DB", "oncopro")
INDIR = "metrics_out"
OUTDIR = "case_studies"
os.makedirs(OUTDIR, exist_ok=True)

# Load per-query NDCG@10 wide
wide = pd.read_csv(os.path.join(INDIR, "per_query_ndcg10.csv"))
models = [c for c in wide.columns if c != "question_id"]

def pick_cases(df: pd.DataFrame) -> Tuple[Tuple[str,str], Tuple[str,str]]:
    # returns ((success_qid, success_model), (failure_qid, failure_model))
    # success
    best_row = None; best_spread = -1.0; best_model = None
    for _, r in df.iterrows():
        vals = [(m, r[m]) for m in models if not pd.isna(r[m])]
        if not vals: continue
        v = [x[1] for x in vals]
        mx, mn = max(v), min(v)
        if mx >= 0.9 and (mx - mn) >= 0.3:
            m_star = max(vals, key=lambda x:x[1])[0]
            return ((r["question_id"], m_star), None)
        if mx > best_spread:
            best_spread = mx
            best_row = r
            best_model = max(vals, key=lambda x:x[1])[0]
    succ = (best_row["question_id"], best_model) if best_row is not None else (None, None)

    # failure
    worst_row = None; worst_max = 10.0; worst_model = None
    for _, r in df.iterrows():
        vals = [(m, r[m]) for m in models if not pd.isna(r[m])]
        if not vals: continue
        mx = max(x[1] for x in vals)
        if mx <= 0.2:
            m_star = max(vals, key=lambda x:x[1])[0]
            return (succ, (r["question_id"], m_star))
        if mx < worst_max:
            worst_max = mx
            worst_row = r
            worst_model = max(vals, key=lambda x:x[1])[0]
    fail = (worst_row["question_id"], worst_model) if worst_row is not None else (None, None)
    return (succ, fail)

succ, fail = pick_cases(wide)

client = MongoClient(MONGO_URI)
db = client[DB]

# Index runs by (model,q)→sorted node_ids
runs_cur = db["runs"].aggregate([
    {"$sort": {"model_name": 1, "question_id": 1, "rank": 1}}
])
runs_by_mq: Dict[Tuple[str,str], List[str]] = {}
for r in runs_cur:
    key = (r["model_name"], str(r["question_id"]))
    runs_by_mq.setdefault(key, []).append(str(r["node_id"]))

# qrels lookup
qrels_by_q: Dict[str, Dict[str, int]] = {}
for r in db["qrels"].find({}):
    qid = str(r["question_id"]); nid = str(r["node_id"])
    qrels_by_q.setdefault(qid, {})[nid] = int(r.get("relevance", 0))

def fetch_question_text(qid: str) -> Tuple[str,str]:
    qdoc = db["questions"].find_one({"_id": qid}) or db["questions"].find_one({"id": qid})
    if not qdoc: return ("", "")
    return (qdoc.get("question_en",""), qdoc.get("question_de",""))

def node_payload(model: str, qid: str, nid: str):
    # find the answer doc and pull node content by id from ordered_nodes or nodes
    ans = db["answers"].find_one({"model_name": model, "question_id": qid})
    if not ans: return {}
    lists = (ans.get("ordered_nodes") or []) + (ans.get("nodes") or [])
    for el in lists:
        # flatten variants
        if isinstance(el, dict):
            cand = None
            if "node" in el and isinstance(el["node"], dict):
                cand = el["node"]
            elif "node" in el and isinstance(el["node"], str):
                if el["node"] == nid: return {"id": nid}
            elif "id" in el or "_id" in el:
                cand = el
            if cand:
                cid = str(cand.get("id") or cand.get("_id") or "")
                if cid == nid:
                    return {
                        "id": cid,
                        "text": cand.get("text","") or cand.get("richText",""),
                        "links": cand.get("links", []),
                        "notes": cand.get("notes",""),
                        "attributes": cand.get("attributes", {}),
                    }
    return {"id": nid}

def render_case(path_md: str, qid: str, model: str, title: str):
    en,de = fetch_question_text(qid)
    ndcg10 = wide.loc[wide["question_id"]==qid, model].values
    ndcg10 = float(ndcg10[0]) if len(ndcg10)>0 and not pd.isna(ndcg10[0]) else None
    ranked = runs_by_mq.get((model, qid), [])[:5]
    rels = qrels_by_q.get(qid, {})
    with open(path_md, "w") as f:
        f.write(f"# {title}\n\n")
        f.write(f"**Question (DE):** {de}\n\n")
        f.write(f"**Question (EN):** {en}\n\n")
        f.write(f"**Model:** {model}\n\n")
        if ndcg10 is not None:
            f.write(f"**NDCG@10:** {ndcg10:.3f}\n\n")
        f.write("## Top-5 Results\n\n")
        for i, nid in enumerate(ranked, start=1):
            rel = rels.get(nid, 0)
            payload = node_payload(model, qid, nid)
            text = (payload.get("text") or "").strip().replace("\n", " ")
            text = (text[:280] + "…") if len(text) > 280 else text
            links = payload.get("links", [])
            link_str = "; ".join(links) if links else ""
            f.write(f"**#{i}**  (relevance={rel})\n\n")
            if text: f.write(f"> {text}\n\n")
            if link_str: f.write(f"_Links:_ {link_str}\n\n")
        f.write("\n")
    print(f"[OK] wrote {path_md}")

if succ[0] and succ[1]:
    render_case(os.path.join(OUTDIR, "success.md"), succ[0], succ[1], "Case Study — Success")

if fail[0] and fail[1]:
    render_case(os.path.join(OUTDIR, "failure.md"), fail[0], fail[1], "Case Study — Failure")
