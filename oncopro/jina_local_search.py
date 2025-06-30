from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from pymongo import MongoClient

from src.utils import DATABASE_NAME, MONGO_URI, embed_text_using_jina_model


def local_cosine_search(query, top_k=5):
    client = MongoClient(MONGO_URI)
    db = client[DATABASE_NAME]
    nodes_collection = db["nodes"]

    all_nodes = list(nodes_collection.find({}, {"_id": 0, "text": 1, "richText": 1, "notes": 1, "links": 1, "attributes": 1, "embedding": 1}))
    query_embedding = np.array(embed_text_using_jina_model(query)).reshape(1, -1)
    node_embeddings = np.array([node['embedding'] for node in all_nodes])

    scores = cosine_similarity(query_embedding, node_embeddings)[0]
    scored_nodes = sorted(zip(all_nodes, scores), key=lambda x: x[1], reverse=True)[:top_k]

    return [{"text": f["text"], "richText": f["richText"], "notes": f["notes"], "links": f["links"], "attributes": f["attributes"], "embedding": f["embedding"], "score": s} for f, s in scored_nodes]


results = local_cosine_search("What are the current guidelines for cervical cancer (Zervixkarzinom)?", top_k=5)
for res in results:
    print(f"{res['text']} ({res['score']:.3f}): {res['richText']} {res['notes']} {res['links']} {res['attributes']}")