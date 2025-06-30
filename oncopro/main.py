"""
Batch embed node documents using Jina model and update MongoDB.

Features
--------
* Skips documents that already contain an `embedding` field.
* Streams through the collection in manageable batches (configurable via `BATCH_SIZE`).
* Uses `bulk_write` for more efficient network round‑trips.
* Displays a `tqdm` progress‑bar and detailed `logging` output so you can see real‑time progress.
"""

import logging
from pymongo import MongoClient, UpdateOne
import nltk
from tqdm import tqdm

from src.utils import DATABASE_NAME, MONGO_URI, embed_text_using_jina_model

nltk.download('punkt_tab')

# Tune this based on the size of your documents and available RAM/CPU
BATCH_SIZE = 500

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()],
)


def generate_node_text(node: dict) -> str:
    """Build a single text block from the various node fields."""
    parts: list[str] = []

    text = (node.get("text") or "").strip()
    if text:
        parts.append(f"Title: {text}")

    rich_text = (node.get("richText") or "").strip()
    if rich_text:
        parts.append(f"Description: {rich_text}")

    notes = (node.get("notes") or "").strip()
    if notes:
        parts.append(f"Notes: {notes}")

    links = node.get("links") or []
    if links:
        str_links = [l for l in links if isinstance(l, str)]
        if str_links:
            parts.append("Links: " + ", ".join(str_links))

    attributes = node.get("attributes") or []
    attr_parts: list[str] = []
    for attr in attributes:
        if not isinstance(attr, dict):
            continue
        name = (attr.get("name") or "").strip()
        value = (attr.get("value") or "").strip()
        if name and value:
            attr_parts.append(f"{name}: {value}")
    if attr_parts:
        parts.append("Attributes: " + ", ".join(attr_parts))

    return " ".join(parts)


def main() -> None:
    client = MongoClient(MONGO_URI)
    db = client[DATABASE_NAME]
    nodes_collection = db["nodes"]

    filter_query = {"embedding": {"$exists": False}}
    total_nodes = nodes_collection.count_documents(filter_query)
    logging.info("Found %s nodes without embeddings", total_nodes)

    cursor = nodes_collection.find(filter_query, batch_size=BATCH_SIZE)

    batch_ops: list[UpdateOne] = []
    processed = 0

    for node in tqdm(cursor, total=total_nodes, desc="Embedding nodes"):
        input_text = generate_node_text(node)
        try:
            embedding = embed_text_using_jina_model(input_text)
        except Exception as exc:  # noqa: BLE001
            logging.exception("Failed to embed node %s: %s", node.get("_id"), exc)
            continue

        batch_ops.append(
            UpdateOne({"_id": node["_id"]}, {"$set": {"embedding": embedding}})
        )

        if len(batch_ops) >= BATCH_SIZE:
            result = nodes_collection.bulk_write(batch_ops, ordered=False)
            processed += result.modified_count
            logging.info("Processed %s / %s nodes (%.2f%%)", processed, total_nodes, processed / total_nodes * 100)
            batch_ops = []

    # write any remaining operations
    if batch_ops:
        result = nodes_collection.bulk_write(batch_ops, ordered=False)
        processed += result.modified_count
        logging.info("Processed %s / %s nodes (%.2f%%)", processed, total_nodes, processed / total_nodes * 100)

    logging.info("✅ Finished updating %s nodes with embeddings.", processed)


if __name__ == "__main__":
    main()
