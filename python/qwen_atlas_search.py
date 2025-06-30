from pymongo import MongoClient

from src.utils import DATABASE_NAME, MONGO_URI, embed_text_using_qwen3_model


def search_fruits(query, top_k=5):
    client = MongoClient(MONGO_URI)
    db = client[DATABASE_NAME]
    fruits_collection = db["fruits"]

    query_embedding = embed_text_using_qwen3_model(query)

    pipeline = [
        {
            "$vectorSearch": {
                "index": "fruits_vector_index",  
                "path": "embedding",
                "queryVector": query_embedding,
                "similarity": "cosine",
                "numCandidates": 100,
                "limit": top_k
            }
        },
        {
            "$project": {
                "_id": 0,
                "name": 1,
                "description": 1,
                "score": {"$meta": "vectorSearchScore"}
            }
        }
    ]

    results = list(fruits_collection.aggregate(pipeline))
    return results



results = search_fruits("Which fruits are citrusy?")
for r in results:
    print(f"{r['name']}: {r['score']:.4f} - {r['description']}")


# {
#   "fields": [
#     {
#       "numDimensions": 768, 768 is for jinaai/jina-embeddings-v2 and 1536 is for openai/text-embedding-3
#       "similarity": "cosine",
#       "type": "vector"
#     }
#   ]
# }