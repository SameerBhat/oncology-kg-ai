import os
import time
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
import torch
load_dotenv()

MAX_TOKENS = 8192
AVG_WORDS_PER_TOKEN = 0.75
MAX_WORDS = int(MAX_TOKENS / AVG_WORDS_PER_TOKEN)


MONGO_URI = os.getenv("DATABASE_URI", "mongodb://localhost:27017")
DATABASE_NAME = "oncopro"

#
def load_jina_model_with_retry(max_retries=3, delay=5):
    device = (
        "cuda" if torch.cuda.is_available()
        else "mps" if torch.backends.mps.is_available()
        else "cpu"
    )
    print("Using device:", device)

    for attempt in range(max_retries):
        try:
            print(f"Loading embedding jina_model... (attempt {attempt + 1}/{max_retries})")
            jina_model = SentenceTransformer(
                "jinaai/jina-embeddings-v4",
                trust_remote_code=True,
                device=device,
                model_kwargs={
                    # "use_flash_attn": False,
                    "attn_implementation": "eager",
                    "default_task": "retrieval",  # use text-embedding task
                    # optionally, torch_dtype/device_map for weight sharding:
                    # "device_map": "auto",
                    # "torch_dtype": torch.bfloat16,
                },
            )
            jina_model.max_seq_length = 8192
            print("Model loaded successfully!")
            return jina_model
        except Exception as e:
            if "429" in str(e) or "rate" in str(e).lower():
                if attempt < max_retries - 1:
                    print(f"Rate limit hit. Waiting {delay} seconds before retry...")
                    time.sleep(delay)
                    delay *= 2
                else:
                    print("Max retries reached.")
                    raise
            else:
                raise

# --- 1. loader with retry ----------------------------------------------------
# def load_qwen3_with_retry(max_retries=3, delay=5):
#     """
#     Load a Qwen3 text-embedding model via Sentence-Transformers.
#     Retries on transient HF errors (429 / 5xx).
#     """
#     for attempt in range(1, max_retries + 1):
#         try:
#             # • Qwen/Qwen3-Embedding-0.6B (≈1 GB, 1 024-d)
#             # • Qwen/Qwen3-Embedding-4B (≈7 GB, 2 560-d)
#             # • Qwen/Qwen3-Embedding-8B (≈14 GB, 4 096-d)
#             print(f"Loading Qwen/Qwen3-Embedding-4B (try {attempt}/{max_retries}) ...")
#             model = SentenceTransformer(
#                 "Qwen/Qwen3-Embedding-4B",
#                 trust_remote_code=True,
#                 model_kwargs={"device_map": "auto"},
#                 tokenizer_kwargs={"padding_side": "left"},
#             )
#             # Qwen3 context = 32 k tokens (way above our chunk size)
#             model.max_seq_length = 32_768
#             print("✓ Qwen3 model ready!")
#             return model
#         except Exception as err:
#             # Detect HF rate-limit or transient errors
#             if any(code in str(err) for code in ("429", "502", "503")) and attempt < max_retries:
#                 print(f"Transient HF error ({err}). Retry in {delay}s …")
#                 time.sleep(delay)
#                 delay *= 2
#             else:
#                 raise   # unrecoverable (e.g. wrong ID or 401 for a private repo)

jina_model = load_jina_model_with_retry()

def embed_text_using_jina_model(text):
    chunks = split_text_into_chunks(text)
    embeddings = jina_model.encode(
        chunks,                      # list[str] from your splitter
        convert_to_tensor=True
    )
    avg = embeddings.mean(dim=0).cpu().tolist()
    return avg

# qwen_model = load_qwen3_with_retry()
#
# def embed_text_using_qwen3_model(text: str, *, prompt_name = None):
#     """
#     Returns 1×d Python list (float) – mean pooling over long documents.
#     Use prompt_name='query' when embedding *queries* (recommended by Qwen3 docs).
#     """
#     chunks = split_text_into_chunks(text)   # <- your existing splitter
#     # Encode all chunks at once (handles batching internally)
#     vecs = qwen_model.encode(
#         chunks,
#         convert_to_tensor=True,
#         prompt_name=prompt_name   # None for docs; 'query' for search queries
#     )
#     # Mean-pool across chunks so one vector represents the whole text
#     return vecs.mean(dim=0).cpu().tolist()
#

def split_text_into_chunks(text, max_words=MAX_WORDS):
    words = text.split()
    chunks = []
    for i in range(0, len(words), max_words):
        chunk = ' '.join(words[i:i + max_words])
        chunks.append(chunk)
    return chunks



