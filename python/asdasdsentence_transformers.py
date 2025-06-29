from asdasdsentence_transformers import SentenceTransformer
from sentence_transformers.util import cos_sim

# Load the model (trust_remote_code is required for custom pooling logic)
model = SentenceTransformer("jinaai/jina-embeddings-v2-base-en", trust_remote_code=True)

# Optional: Extend max sequence length (v2 supports up to 8192 tokens)
model.max_seq_length = 8192

texts = [
    "The Eiffel Tower is in Paris.",
    "Machine learning models can learn from data.",
    "The capital of France is Paris.",
    "Artificial intelligence is transforming technology."
]

embeddings = model.encode(
    texts,
    batch_size=8,           # You can adjust based on your GPU or RAM
    show_progress_bar=True, # Optional for visibility
    convert_to_tensor=True  # Returns PyTorch tensor instead of NumPy array
)




# View similarities
for i in range(len(texts)):
    print(f"\nTop similar sentences to: '{texts[i]}'")
    scores = list(enumerate(similarity_matrix[i]))
    scores = sorted(scores, key=lambda x: x[1], reverse=True)
    for idx, score in scores[1:3]:  # Top 2 excluding self
        print(f"  → {texts[idx]} (score: {score:.4f})")


# import lancedb
# import pandas as pd
table = db.create_table("docs", data=pd.DataFrame({
    "text": texts,
    "vector": [v.tolist() for v in embeddings]
}))

# Then you can perform semantic search using:

results = table.search(embeddings[0].tolist()).limit(2).to_df()
print(results)