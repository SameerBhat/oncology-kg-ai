from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from pymongo import MongoClient

from src.utils import DATABASE_NAME, MONGO_URI, embed_text_using_jina_model


def local_cosine_search(query, top_k=5):
    client = MongoClient(MONGO_URI)
    db = client[DATABASE_NAME]
    fruits_collection = db["fruits"]

    all_fruits = list(fruits_collection.find({}, {"_id": 0, "name": 1, "embedding": 1, "description": 1}))
    query_embedding = np.array(embed_text_using_jina_model(query)).reshape(1, -1)
    fruit_embeddings = np.array([fruit['embedding'] for fruit in all_fruits])

    scores = cosine_similarity(query_embedding, fruit_embeddings)[0]
    scored_fruits = sorted(zip(all_fruits, scores), key=lambda x: x[1], reverse=True)[:top_k]

    return [{"name": f["name"], "description": f["description"], "score": score} for f, score in scored_fruits]


results = local_cosine_search("Which fruits are citrusy?", top_k=5)
for res in results:
    print(f"{res['name']} ({res['score']:.3f}): {res['description']}")