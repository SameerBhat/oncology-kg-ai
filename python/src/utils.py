import os
import time
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

# Load environment variables from .env file
load_dotenv()

MAX_TOKENS = 8192
AVG_WORDS_PER_TOKEN = 0.75
MAX_WORDS = int(MAX_TOKENS / AVG_WORDS_PER_TOKEN)

# Load environment variables (or hardcode if preferred)
MONGO_URI = os.getenv("DATABASE_URI", "mongodb://localhostchanged:27017")
DATABASE_NAME = "testvectors"

print(f"Using MongoDB URI: {MONGO_URI}")
# Load embedding model once at module level with retry logic
def load_model_with_retry(max_retries=3, delay=5):
    for attempt in range(max_retries):
        try:
            print(f"Loading embedding model... (attempt {attempt + 1}/{max_retries})")
            model = SentenceTransformer("jinaai/jina-embeddings-v2-base-en", trust_remote_code=True)
            model.max_seq_length = 8192  # Set max length explicitly for Jina v2
            print("Model loaded successfully!")
            return model
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

model = load_model_with_retry()

def embed_text(text):
    chunks = split_text_into_chunks(text)
    embeddings = model.encode(chunks, convert_to_tensor=True)
    avg_embedding = embeddings.mean(dim=0)
    return avg_embedding.cpu().tolist()

def split_text_into_chunks(text, max_words=MAX_WORDS):
    words = text.split()
    chunks = []
    for i in range(0, len(words), max_words):
        chunk = ' '.join(words[i:i + max_words])
        chunks.append(chunk)
    return chunks