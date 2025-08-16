#!/usr/bin/env python3
"""
Benchmark embedding models for efficiency metrics.
Generates metrics_out/efficiency.csv with real performance data.

Measures:
- Query latency (median time to embed a search query)
- Index size (approximate memory usage)
- Build time (time to embed a batch of documents)
"""

import os
import csv
import time
import logging
import statistics
import sys
from typing import List, Dict, Any, Optional
import gc

from src import (
    embed_text,
    MongoDBClient,
    EMBEDDING_MODEL,
    get_embedding_model
)
from src.embedding_utils import setup_logging
from src.embeddings.factory import EmbeddingModelFactory


def measure_query_latency(model_name: str, test_queries: List[str], num_runs: int = 10) -> float:
    """Measure median query latency for a model."""
    logging.info(f"Measuring query latency for {model_name}...")
    
    # Get embedding function for this model
    embed_func = lambda text: embed_text(text, model_name=model_name)
    
    # Warm up with one query
    embed_func(test_queries[0])
    
    latencies = []
    for i in range(num_runs):
        query = test_queries[i % len(test_queries)]
        
        start_time = time.time()
        embed_func(query)
        end_time = time.time()
        
        latency_ms = (end_time - start_time) * 1000
        latencies.append(latency_ms)
        
        # Force garbage collection to get consistent measurements
        gc.collect()
    
    median_latency = statistics.median(latencies)
    logging.info(f"  Median latency: {median_latency:.2f} ms")
    return median_latency


def estimate_index_size(model_name: str, sample_texts: List[str]) -> float:
    """Estimate index size by measuring memory usage of embeddings."""
    logging.info(f"Estimating index size for {model_name}...")
    
    # Get embedding function for this model
    embed_func = lambda text: embed_text(text, model_name=model_name)
    
    # Generate embeddings for sample texts
    embeddings = []
    for text in sample_texts:
        embedding = embed_func(text)
        embeddings.append(embedding)
    
    # Estimate size per embedding (in bytes)
    if embeddings:
        import numpy as np
        sample_embedding = np.array(embeddings[0])
        bytes_per_embedding = sample_embedding.nbytes
        dimension = len(sample_embedding)
        
        # Estimate for 1000 documents (typical small database)
        estimated_docs = 1000
        total_bytes = estimated_docs * bytes_per_embedding
        size_mb = total_bytes / (1024 * 1024)
        
        logging.info(f"  Embedding dimension: {dimension}")
        logging.info(f"  Estimated index size: {size_mb:.1f} MB (for {estimated_docs} docs)")
        return size_mb
    
    return 0.0


def measure_build_time(model_name: str, sample_texts: List[str]) -> float:
    """Measure time to embed a batch of documents."""
    logging.info(f"Measuring build time for {model_name}...")
    
    # Get embedding function for this model
    embed_func = lambda text: embed_text(text, model_name=model_name)
    
    start_time = time.time()
    
    # Embed all sample texts
    for text in sample_texts:
        embed_func(text)
    
    end_time = time.time()
    build_time = end_time - start_time
    
    logging.info(f"  Build time: {build_time:.2f} s for {len(sample_texts)} documents")
    return build_time


def get_sample_data() -> tuple[List[str], List[str]]:
    """Get sample queries and documents from the database."""
    logging.info("Fetching sample data from database...")
    
    queries = [
        "What are the symptoms of lung cancer?",
        "How is breast cancer treated?",
        "What causes prostate cancer?",
        "What are the side effects of chemotherapy?",
        "How is cancer diagnosed?",
        "What is immunotherapy?",
        "What are tumor markers?",
        "How does radiation therapy work?",
        "What is palliative care?",
        "What are the stages of cancer?"
    ]
    
    documents = []
    
    try:
        with MongoDBClient() as db_client:
            collection = db_client.get_collection("nodes")
            
            # Get sample documents from database
            cursor = collection.find(
                {"text": {"$exists": True, "$ne": ""}},
                {"text": 1}
            ).limit(20)
            
            for doc in cursor:
                text = doc.get("text", "").strip()
                if text and len(text) > 50:  # Only meaningful text
                    documents.append(text[:500])  # Limit length for consistency
            
            logging.info(f"Found {len(documents)} sample documents")
            
    except Exception as e:
        logging.warning(f"Could not fetch documents from database: {e}")
        
        # Fallback to sample medical texts
        documents = [
            "Cancer is a group of diseases involving abnormal cell growth with the potential to invade or spread to other parts of the body.",
            "Chemotherapy is a type of cancer treatment that uses one or more anti-cancer drugs as part of a standardized chemotherapy regimen.",
            "Radiation therapy uses high-energy particles or waves, such as x-rays, gamma rays, electron beams, or protons, to destroy or damage cancer cells.",
            "Immunotherapy is a type of cancer treatment that helps your immune system fight cancer.",
            "Tumor markers are substances found in blood, urine, or body tissues that can be elevated by the presence of one or more types of cancer.",
            "Palliative care is specialized medical care focused on providing relief from the symptoms and stress of a serious illness.",
            "Metastasis is the spread of cancer cells to new areas of the body, often by way of the lymph system or bloodstream.",
            "Oncology is a branch of medicine that deals with the prevention, diagnosis, and treatment of cancer.",
            "A biopsy is a procedure to remove a piece of tissue or a sample of cells from your body so that it can be tested in a laboratory.",
            "Staging describes the severity of a person's cancer based on the magnitude of the original tumor as well as the extent cancer has spread in the body."
        ]
    
    return queries, documents


def benchmark_model(model_name: str, test_queries: List[str], sample_docs: List[str]) -> Dict[str, float]:
    """Benchmark a single model and return efficiency metrics."""
    logging.info(f"\n{'='*50}")
    logging.info(f"Benchmarking model: {model_name}")
    logging.info(f"{'='*50}")
    
    try:
        # Measure query latency
        median_latency = measure_query_latency(model_name, test_queries, num_runs=5)
        
        # Estimate index size  
        index_size = estimate_index_size(model_name, sample_docs[:5])  # Use fewer docs for speed
        
        # Measure build time
        build_time = measure_build_time(model_name, sample_docs[:5])  # Use fewer docs for speed
        
        return {
            "model": model_name,
            "median_latency_ms": round(median_latency, 2),
            "index_size_mb": round(index_size, 2),
            "build_time_s": round(build_time, 2)
        }
        
    except Exception as e:
        logging.error(f"Failed to benchmark {model_name}: {e}")
        return None


def main():
    """Main benchmarking function."""
    setup_logging()
    
    output_file = "metrics_out/efficiency.csv"
    os.makedirs("metrics_out", exist_ok=True)
    
    logging.info("Starting embedding model efficiency benchmarking...")
    
    # Get sample data
    test_queries, sample_docs = get_sample_data()
    
    if not sample_docs:
        logging.error("No sample documents available for benchmarking")
        sys.exit(1)
    
    # Get available models
    available_models = EmbeddingModelFactory.list_available_models()
    logging.info(f"Available models: {', '.join(available_models)}")
    
    # Benchmark each model
    results = []
    
    for model_name in available_models:
        result = benchmark_model(model_name, test_queries, sample_docs)
        if result:
            results.append(result)
    
    if not results:
        logging.error("No successful benchmarks completed")
        sys.exit(1)
    
    # Write results to CSV
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ["model", "median_latency_ms", "index_size_mb", "build_time_s"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        
        writer.writeheader()
        for result in results:
            writer.writerow(result)
    
    logging.info(f"\n{'='*50}")
    logging.info(f"Benchmarking complete! Results written to {output_file}")
    logging.info(f"{'='*50}")
    
    # Print summary
    print("\nEfficiency Summary:")
    print("-" * 70)
    print(f"{'Model':<15} {'Latency (ms)':<12} {'Index (MB)':<12} {'Build (s)':<10}")
    print("-" * 70)
    for result in results:
        print(f"{result['model']:<15} {result['median_latency_ms']:<12} "
              f"{result['index_size_mb']:<12} {result['build_time_s']:<10}")


if __name__ == "__main__":
    main()
