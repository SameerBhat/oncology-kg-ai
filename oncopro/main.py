import logging
from pymongo import MongoClient
from tqdm import tqdm

from src.utils import DATABASE_NAME, MONGO_URI, embed_text_using_jina_model

import nltk
nltk.download('punkt_tab')

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


def log_progress(processed: int, total: int) -> None:
    """Log a nicely formatted progress line with totals and remaining count."""
    remaining = total - processed
    percentage = (processed / total * 100) if total else 0
    logging.info(
        "Processed %s / %s nodes (%.2f%%) – %s left",
        processed,
        total,
        percentage,
        remaining,
    )


def main() -> None:
    client = MongoClient(MONGO_URI)
    db = client[DATABASE_NAME]
    nodes_collection = db["nodes"]

    filter_query = {"embedding": {"$exists": False}}
    total_nodes = nodes_collection.count_documents(filter_query)
    logging.info("Found %s nodes without embeddings", total_nodes)

    cursor = nodes_collection.find(filter_query)

    processed = 0

    for node in tqdm(cursor, total=total_nodes, desc="Embedding nodes"):
        input_text = generate_node_text(node)
        try:
            embedding = embed_text_using_jina_model(input_text)
        except Exception as exc:  # noqa: BLE001
            logging.exception("Failed to embed node %s: %s", node.get("_id"), exc)
            continue

        # Update the node immediately
        nodes_collection.update_one(
            {"_id": node["_id"]}, 
            {"$set": {"embedding": embedding}}
        )
        processed += 1
        
        # Log progress every 100 nodes
        if processed % 100 == 0:
            log_progress(processed, total_nodes)

    logging.info("✅ Finished embedding %s nodes.", processed)


if __name__ == "__main__":
    main()
