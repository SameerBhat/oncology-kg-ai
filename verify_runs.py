#!/usr/bin/env python3
"""
Verify the runs collection created by flatten_runs_from_answers.py
"""
import os
from pymongo import MongoClient

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DB = os.getenv("DB", "oncopro")

client = MongoClient(MONGO_URI)
db = client[DB]
runs = db["runs"]

# Check total count
total_runs = runs.count_documents({})
print(f"Total runs in collection: {total_runs}")

# Check unique questions
unique_questions = len(list(runs.distinct("question_id")))
print(f"Unique questions: {unique_questions}")

# Check unique models
unique_models = list(runs.distinct("model_name"))
print(f"Unique models: {unique_models}")

# Show sample data
print("\nSample runs:")
for doc in runs.find({}).limit(10):
    print(f"  Q: {doc.get('question_id')[:20]}..., Model: {doc.get('model_name')}, Node: {doc.get('node_id')}, Rank: {doc.get('rank')}, Score: {doc.get('score')}")

# Check for any issues
print("\nData validation:")

# Check for missing node_ids
missing_node_ids = runs.count_documents({"node_id": {"$in": [None, ""]}})
print(f"Runs with missing node_ids: {missing_node_ids}")

# Check for missing question_ids
missing_q_ids = runs.count_documents({"question_id": {"$in": [None, ""]}})
print(f"Runs with missing question_ids: {missing_q_ids}")

# Check rank distribution
rank_stats = list(runs.aggregate([
    {"$group": {"_id": "$rank", "count": {"$sum": 1}}},
    {"$sort": {"_id": 1}},
    {"$limit": 20}
]))
print(f"Rank distribution (first 20): {rank_stats}")

# Check if any scores are available
runs_with_scores = runs.count_documents({"score": {"$ne": None}})
print(f"Runs with scores: {runs_with_scores}")
