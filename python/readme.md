
This creates a folder called venv which contains the isolated Python environment.
python3 -m venv venv

# To activate the virtual environment, run the following command:
source venv/bin/activate


You can also generate it later using:


pip freeze > requirements.txt


Install all packages listed in requirements.txt:


pip install -r requirements.txt

Deactivate When Done

deactivate


OpenAI embedding models
text-embedding-3-small $0.02
text-embedding-3-large $0.13 
text-embedding-ada-002 $0.10

📊 Summary
Model	Embedding Size	Max Input Tokens
text‑embedding‑3‑small	1,536 dims	8,191 tokens
text‑embedding‑3‑large	3,072 dims	8,191 tokens
text‑embedding‑ada‑002	1,536 dims	8,191 tokens

All three models allow up to 8,191 tokens in a single embedding request.


Even though the vector format looks the same, the quality and meaning of those numbers depend on the model:

Model	Vector Size	Semantic Quality	Speed/Cost
all-MiniLM-L6-v2	384	Good (small, efficient)	Fast, free
text-embedding-ada-002	1,536	Strong	Low-cost (OpenAI)
text-embedding-3-small	1,536	Newer, better than Ada	Low-cost (OpenAI)
text-embedding-3-large	3,072	Highest quality	Higher cost