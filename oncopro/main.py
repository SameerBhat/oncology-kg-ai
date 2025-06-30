"""
Batch‑embed node documents using Jina model and update MongoDB **fast**.

What’s new (v2)
---------------
* **Concurrent embedding** via `ThreadPoolExecutor` (default 8 workers).  I/O‑bound HTTP calls can now saturate your outbound bandwidth and remote replicas.
* **Batched DB writes** stay as `bulk_write`, but now we also process embedding in the same batch, so each `UpdateOne` round‑trips only every `BATCH_SIZE` nodes.
* Progress bar still shows live throughput, but you should see ~*workers ×* speed‑up (network permitting).
* Re‑factored into smaller helpers for clarity.
"""

from __future__ import annotations

import logging
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List

import nltk
from pymongo import MongoClient, UpdateOne
from tqdm import tqdm

from src.utils import DATABASE_NAME, MONGO_URI, embed_text_using_jina_model

nltk.download('punkt_tab')

# ─────────────────────────── Configuration ────────────────────────────
BATCH_SIZE = int(os.getenv("EMBED_BATCH", "500"))  # docs per DB bulk‑write
MAX_WORKERS = int(os.getenv("EMBED_WORKERS", "8"))  # concurrent embed calls

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()],
)

# ───────────────────────────── Helpers ────────────────────────────────

def generate_node_text(node: dict) -> str:
    """Concat relevant node fields into one text block."""
    parts: List[str] = []

    for key, label in (
            ("text", "Title"),
            ("richText", "Description"),
            ("notes", "Notes"),
    ):
        val = (node.get(key) or "").strip()
        if val:
            parts.append(f"{label}: {val}")

    links = [l for l in node.get("links") or [] if isinstance(l, str)]
    if links:
        parts.append("Links: " + ", ".join(links))

    attr_parts: List[str] = []
    for attr in node.get("attributes") or []:
        if not isinstance(attr, dict):
            continue
        name = (attr.get("name") or "").strip()
        value = (attr.get("value") or "").strip()
        if name and value:
            attr_parts.append(f"{name}: {value}")
    if attr_parts:
        parts.append("Attributes: " + ", ".join(attr_parts))

    return " ".join(parts)


def embed_single(node: dict):
    """Return (_id, embedding) or None on failure."""
    try:
        text = generate_node_text(node)
        emb = embed_text_using_jina_model(text)
        return node["_id"], emb
    except Exception as exc:  # noqa: BLE001
        logging.exception("Embedding failed for %s: %s", node.get("_id"), exc)
        return None


# ────────────────────────────── Main ─────────────────────────────────

def main() -> None:
    client = MongoClient(MONGO_URI)
    db = client[DATABASE_NAME]
    nodes_collection = db["nodes"]

    query = {"embedding": {"$exists": False}}
    total = nodes_collection.count_documents(query)
    logging.info("Found %s nodes without embeddings", total)

    cursor = nodes_collection.find(query, batch_size=BATCH_SIZE)

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool, tqdm(
            total=total,
            desc="Embedding nodes",
            unit="node",
    ) as pbar:
        batch_nodes: List[dict] = []
        futures: List = []
        processed = 0

        for node in cursor:
            batch_nodes.append(node)
            if len(batch_nodes) >= BATCH_SIZE:
                futures.extend(pool.submit(embed_single, n) for n in batch_nodes)
                batch_nodes = []

                updates = _collect_and_write(futures, nodes_collection)
                processed += updates
                pbar.update(updates)
                futures = []

        # handle leftovers
        if batch_nodes:
            futures.extend(pool.submit(embed_single, n) for n in batch_nodes)
        if futures:
            updates = _collect_and_write(futures, nodes_collection)
            processed += updates
            pbar.update(updates)

    logging.info("✅ Finished updating %s nodes with embeddings.", processed)


def _collect_and_write(futures, collection):
    """Gather completed futures, build UpdateOne docs, write bulk, return #updates."""
    ops: List[UpdateOne] = []
    for fut in as_completed(futures):
        result = fut.result()
        if result:
            _id, emb = result
            ops.append(UpdateOne({"_id": _id}, {"$set": {"embedding": emb}}))

    if not ops:
        return 0

    res = collection.bulk_write(ops, ordered=False)
    return res.modified_count


if __name__ == "__main__":
    main()
