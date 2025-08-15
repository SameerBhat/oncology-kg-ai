#!/usr/bin/env python3

import os
from pymongo import MongoClient

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DB = os.getenv("DB", "oncopro")

client = MongoClient(MONGO_URI)
db = client[DB]
qrels = db["qrels"]

# Check how many qrels exist
total_count = qrels.count_documents({})
print(f"Total qrels in database: {total_count}")

# Check by version
qrels_v1_count = qrels.count_documents({"qrels_version": "v1"})
print(f"Qrels with version 'v1': {qrels_v1_count}")

# Show some sample data
print("\nSample qrels:")
for doc in qrels.find({}).limit(5):
    print(f"  Question: {doc.get('question_id')}, Node: {doc.get('node_id')}, Relevance: {doc.get('relevance')}")

# Check unique questions
unique_questions = len(list(qrels.distinct("question_id")))
print(f"\nUnique questions with qrels: {unique_questions}")

# Check answers collection to see what data we're working with
answers = db["answers"]
answers_count = answers.count_documents({"completed": True})
print(f"Completed answers in database: {answers_count}")

print("\nSample answers:")
for doc in answers.find({"completed": True}).limit(2):
    qid = str(doc.get("question_id") or doc.get("question"))
    nodes = doc.get("ordered_nodes") or doc.get("nodes") or []
    print(f"  Question: {qid}, Nodes count: {len(nodes)}")
