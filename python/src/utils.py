import os
import time
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer, AutoModel
import torch
# Load environment variables from .env file
load_dotenv()

MAX_TOKENS = 8192
AVG_WORDS_PER_TOKEN = 0.75
MAX_WORDS = int(MAX_TOKENS / AVG_WORDS_PER_TOKEN)

# Load environment variables (or hardcode if preferred)
# print(f"DATABASE_URI env var: {os.getenv('DATABASE_URI')}")
# print(f"All DATABASE related env vars: {[k for k in os.environ.keys() if 'DATABASE' in k.upper()]}")
MONGO_URI = os.getenv("DATABASE_URI", "mongodb://localhost:27017")
DATABASE_NAME = "testvectors"

# print(f"Using MongoDB URI: {MONGO_URI}")
# Load embedding model once at module level with retry logic
def load_jina_model_with_retry(max_retries=3, delay=5):
    for attempt in range(max_retries):
        try:
            print(f"Loading embedding jina_model... (attempt {attempt + 1}/{max_retries})")
            jina_model = SentenceTransformer("jinaai/jina-embeddings-v2-base-en", trust_remote_code=True)
            jina_model.max_seq_length = 8192  # Set max length explicitly for Jina v2
            print("Model loaded successfully!")
            return jina_model
        except Exception as e:
            if "429" in str(e) or "rate" in str(e).lower():
                if attempt < max_retries - 1:
                    print(f"Rate limit hit. Waiting {delay} seconds before retry...")
                    time.sleep(delay)
                    delay *= 2  # Exponential backoff
                else:
                    print("Max retries reached. Please try again later.")
                    raise
            else:
                raise
def load_qwen3_with_retry(max_retries=3, delay=5):
    model_name = "Qwen/Qwen3-Embedding-0.6B"
    for attempt in range(max_retries):
        try:
            print(f"Loading Qwen3 embedding model... (attempt {attempt + 1}/{max_retries})")
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            model = AutoModel.from_pretrained(model_name)
            print("Qwen3 model loaded successfully!")
            return tokenizer, model
        except Exception as e:
            print(f"Error loading Qwen3: {e}")
            if attempt < max_retries - 1:
                print(f"Retrying in {delay} seconds...")
                time.sleep(delay)
                delay *= 2
            else:
                raise
# jina_model = load_jina_model_with_retry()
qwen_tokenizer, qwen_model = load_qwen3_with_retry()

# def embed_text_using_jina_model(text):
#     chunks = split_text_into_chunks(text)
#     embeddings = jina_model.encode(chunks, convert_to_tensor=True)
#     avg_embedding = embeddings.mean(dim=0)
#     return avg_embedding.cpu().tolist()


def embed_text_using_qwen3_model(text):
    chunks = split_text_into_chunks(text)
    all_embeddings = []

    for chunk in chunks:
        inputs = qwen_tokenizer(chunk, return_tensors="pt", truncation=True, padding=True)
        with torch.no_grad():
            outputs = qwen_model(**inputs)
            hidden_states = outputs.last_hidden_state
            attention_mask = inputs["attention_mask"]
            input_mask_expanded = attention_mask.unsqueeze(-1).expand(hidden_states.size()).float()
            sum_embeddings = torch.sum(hidden_states * input_mask_expanded, 1)
            sum_mask = torch.clamp(input_mask_expanded.sum(1), min=1e-9)
            mean_embedding = sum_embeddings / sum_mask
            all_embeddings.append(mean_embedding)

    stacked = torch.stack(all_embeddings)
    final_embedding = stacked.mean(dim=0)
    return final_embedding.squeeze(0).cpu().tolist()


def split_text_into_chunks(text, max_words=MAX_WORDS):
    words = text.split()
    chunks = []
    for i in range(0, len(words), max_words):
        chunk = ' '.join(words[i:i + max_words])
        chunks.append(chunk)
    return chunks



