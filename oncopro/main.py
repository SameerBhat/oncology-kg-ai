
from pymongo import MongoClient
import nltk
from src.utils import DATABASE_NAME, MONGO_URI, embed_text_using_jina_model

nltk.download('punkt_tab')



def generate_node_text(node):
    parts = []

    text = node.get('text', '').strip()
    if text:
        parts.append(f"Title: {text}")

    rich_text = node.get('richText', '').strip()
    if rich_text:
        parts.append(f"Description: {rich_text}")

    notes = node.get('notes', '').strip()
    if notes:
        parts.append(f"Notes: {notes}")

    links = node.get('links', [])
    if isinstance(links, list) and links:
        parts.append("Links: " + ', '.join(link for link in links if isinstance(link, str)))

    attributes = node.get('attributes', [])
    if isinstance(attributes, list):
        attr_parts = []
        for attr in attributes:
            if isinstance(attr, dict):
                name = attr.get('name', '').strip()
                value = attr.get('value', '').strip()
                if name and value:
                    attr_parts.append(f"{name}: {value}")
        if attr_parts:
            parts.append("Attributes: " + ', '.join(attr_parts))

    return ' '.join(parts)

def main():
    client = MongoClient(MONGO_URI)
    db = client[DATABASE_NAME]
    nodes_collection = db["nodes"]

    # Get all nodes from the collection, fetch nodes where embedding is missing
    nodes = list(nodes_collection.find({}))  # Fetch all documents
    documents_updated = 0

    for node in nodes:
        input_text = generate_node_text(node)
        embedding = embed_text_using_jina_model(input_text)

        # Update the node document with the new embedding
        result = nodes_collection.update_one(
            {"_id": node["_id"]},
            {"$set": {"embedding": embedding}},
            upsert=False  # Don't insert new if not found
        )
        documents_updated += result.modified_count

    print(f"✅ Updated {documents_updated} nodes with embeddings.")


if __name__ == "__main__":
    main()