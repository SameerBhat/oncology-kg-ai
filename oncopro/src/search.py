"""
Search operations for querying embeddings using cosine similarity.
Supports model-specific search optimizations and configurations.
"""
import logging
import numpy as np
from typing import List, Dict, Any, Optional, Union
from sklearn.metrics.pairwise import cosine_similarity

from .database import MongoDBClient
from .utils import embed_text, get_embedding_model
from .config import EMBEDDING_MODEL


logger = logging.getLogger(__name__)


class SearchManager:
    """Manager class for search operations using cosine similarity."""
    
    def __init__(self, client: Optional[MongoDBClient] = None, collection_name: str = "nodes", 
                 embedding_model_name: Optional[str] = None):
        """
        Initialize SearchManager.
        
        Args:
            client: MongoDBClient instance. If None, creates a new one.
            collection_name: Name of the nodes collection
            embedding_model_name: Name of embedding model to use. If None, uses EMBEDDING_MODEL from config.
        """
        self.client = client or MongoDBClient()
        self.collection_name = collection_name
        self.embedding_model_name = embedding_model_name or EMBEDDING_MODEL
        self._collection = None
        self._embedding_model = None
    
    @property
    def collection(self):
        """Get the nodes collection."""
        if self._collection is None:
            self._collection = self.client.get_collection(self.collection_name)
        return self._collection
    
    @property
    def embedding_model(self):
        """Get the embedding model instance."""
        if self._embedding_model is None:
            self._embedding_model = get_embedding_model(self.embedding_model_name)
        return self._embedding_model
    
    def get_search_stats(self) -> Dict[str, int]:
        """
        Get statistics about searchable nodes.
        
        Returns:
            Dictionary with search statistics
        """
        total_nodes = self.collection.count_documents({})
        nodes_with_embeddings = self.collection.count_documents({"embedding": {"$exists": True}})
        nodes_without_embeddings = total_nodes - nodes_with_embeddings
        
        stats = {
            "total_nodes": total_nodes,
            "total_nodes_with_embeddings": nodes_with_embeddings,
            "nodes_without_embeddings": nodes_without_embeddings,
            "embedding_model": self.embedding_model_name
        }
        
        logger.info(f"Search stats: {stats}")
        return stats
    
    def _preprocess_query(self, query: str) -> str:
        """
        Preprocess query based on model-specific requirements.
        
        Args:
            query: Raw query string
            
        Returns:
            Preprocessed query string
        """
        # Model-specific preprocessing can be added here
        model_id = self.embedding_model.MODEL_ID
        
        # Example of model-specific preprocessing
        if model_id == "jina4":
            # Jina models might benefit from specific query formatting
            # This is a placeholder for any model-specific logic
            pass
        elif model_id == "openai":
            # OpenAI models might have different requirements
            pass
        elif model_id == "nvembedv2":
            # NVIDIA models might need special handling
            pass
        
        # Apply any global query preprocessing
        query = query.strip()
        
        return query
    
    def _calculate_similarity(self, query_embedding: np.ndarray, node_embeddings: np.ndarray) -> np.ndarray:
        """
        Calculate similarity scores between query and node embeddings.
        Can be overridden for model-specific similarity calculations.
        
        Args:
            query_embedding: Query embedding vector
            node_embeddings: Array of node embedding vectors
            
        Returns:
            Array of similarity scores
        """
        model_id = self.embedding_model.MODEL_ID
        
        # Most models use cosine similarity, but some might benefit from different metrics
        if model_id in ["jina4", "qwen34b", "bgem3", "gte", "mpnetbase2", "nomicv2"]:
            # Standard cosine similarity for most models
            return cosine_similarity(query_embedding, node_embeddings)[0]
        elif model_id == "nvembedv2":
            # NVIDIA models might benefit from different similarity metrics
            # For now, using cosine similarity but could be customized
            return cosine_similarity(query_embedding, node_embeddings)[0]
        elif model_id == "openai":
            # OpenAI embeddings are optimized for cosine similarity
            return cosine_similarity(query_embedding, node_embeddings)[0]
        else:
            # Default to cosine similarity
            return cosine_similarity(query_embedding, node_embeddings)[0]
    
    def cosine_search(self, query: str, top_k: int = 5, threshold: float = 0.0) -> List[Dict[str, Any]]:
        """
        Perform cosine similarity search using the configured embedding model.
        
        Args:
            query: Search query text
            top_k: Number of top results to return
            threshold: Minimum similarity score threshold
            
        Returns:
            List of search results with content, score, and metadata
        """
        try:
            # Preprocess query based on model requirements
            processed_query = self._preprocess_query(query)
            
            # Generate query embedding using the configured model
            logger.info(f"Generating embedding for query using {self.embedding_model_name}: {processed_query[:100]}...")
            query_embedding = embed_text(processed_query)
            
            if query_embedding is None:
                raise ValueError("Failed to generate query embedding")
            
            # Convert to numpy array and reshape for similarity calculation
            query_embedding = np.array(query_embedding).reshape(1, -1)
            
            # Get all nodes with embeddings
            nodes_with_embeddings = list(self.collection.find(
                {"embedding": {"$exists": True}},
                {"_id": 1, "embedding": 1, "content": 1, "metadata": 1}
            ))
            
            if not nodes_with_embeddings:
                logger.warning("No nodes with embeddings found")
                return []
            
            logger.info(f"Found {len(nodes_with_embeddings)} nodes with embeddings")
            
            # Extract embeddings and prepare data
            node_embeddings = []
            node_data = []
            
            for node in nodes_with_embeddings:
                embedding = node.get("embedding")
                if embedding and len(embedding) > 0:
                    node_embeddings.append(embedding)
                    node_data.append({
                        "_id": str(node["_id"]),
                        "content": node.get("content", ""),
                        "metadata": node.get("metadata", {})
                    })
            
            if not node_embeddings:
                logger.warning("No valid embeddings found")
                return []
            
            # Convert to numpy array for similarity calculation
            node_embeddings = np.array(node_embeddings)
            
            # Calculate similarities using model-specific method
            similarities = self._calculate_similarity(query_embedding, node_embeddings)
            
            # Create scored results
            scored_results = []
            for i, (node, score) in enumerate(zip(node_data, similarities)):
                if score >= threshold:
                    scored_results.append({
                        "_id": node["_id"],
                        "content": node["content"],
                        "metadata": node["metadata"],
                        "score": float(score),
                        "model_used": self.embedding_model_name
                    })
            
            # Sort by score in descending order and return top_k
            scored_results.sort(key=lambda x: x["score"], reverse=True)
            results = scored_results[:top_k]
            
            logger.info(f"Returning {len(results)} results (top_k={top_k}, threshold={threshold})")
            return results
            
        except Exception as e:
            logger.exception(f"Error during cosine search: {e}")
            raise
    
    def search_by_content(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search for nodes by content similarity using embeddings.
        
        Args:
            query: Search query text
            top_k: Number of top results to return
            
        Returns:
            List of search results
        """
        return self.cosine_search(query, top_k=top_k)
    
    def get_similar_nodes(self, node_id: str, top_k: int = 5, exclude_self: bool = True) -> List[Dict[str, Any]]:
        """
        Find nodes similar to a given node using its embedding.
        
        Args:
            node_id: ID of the reference node
            top_k: Number of similar nodes to return
            exclude_self: Whether to exclude the reference node from results
            
        Returns:
            List of similar nodes
        """
        try:
            # Get the reference node
            from bson import ObjectId
            reference_node = self.collection.find_one(
                {"_id": ObjectId(node_id), "embedding": {"$exists": True}},
                {"embedding": 1, "content": 1}
            )
            
            if not reference_node:
                logger.warning(f"Node {node_id} not found or has no embedding")
                return []
            
            # Use the reference node's embedding as query
            reference_embedding = reference_node["embedding"]
            reference_embedding = np.array(reference_embedding).reshape(1, -1)
            
            # Get all other nodes with embeddings
            filter_query = {"embedding": {"$exists": True}}
            if exclude_self:
                filter_query["_id"] = {"$ne": ObjectId(node_id)}
            
            nodes_with_embeddings = list(self.collection.find(
                filter_query,
                {"_id": 1, "embedding": 1, "content": 1, "metadata": 1}
            ))
            
            if not nodes_with_embeddings:
                return []
            
            # Extract embeddings and calculate similarities
            node_embeddings = []
            node_data = []
            
            for node in nodes_with_embeddings:
                embedding = node.get("embedding")
                if embedding and len(embedding) > 0:
                    node_embeddings.append(embedding)
                    node_data.append({
                        "_id": str(node["_id"]),
                        "content": node.get("content", ""),
                        "metadata": node.get("metadata", {})
                    })
            
            if not node_embeddings:
                return []
            
            node_embeddings = np.array(node_embeddings)
            similarities = self._calculate_similarity(reference_embedding, node_embeddings)
            
            # Create and sort results
            scored_results = []
            for node, score in zip(node_data, similarities):
                scored_results.append({
                    "_id": node["_id"],
                    "content": node["content"],
                    "metadata": node["metadata"],
                    "score": float(score),
                    "model_used": self.embedding_model_name
                })
            
            scored_results.sort(key=lambda x: x["score"], reverse=True)
            return scored_results[:top_k]
            
        except Exception as e:
            logger.exception(f"Error finding similar nodes: {e}")
            raise
    
    def batch_search(self, queries: List[str], top_k: int = 5, threshold: float = 0.0) -> Dict[str, List[Dict[str, Any]]]:
        """
        Perform batch search for multiple queries.
        
        Args:
            queries: List of search queries
            top_k: Number of top results per query
            threshold: Minimum similarity score threshold
            
        Returns:
            Dictionary mapping each query to its search results
        """
        results = {}
        for i, query in enumerate(queries):
            logger.info(f"Processing batch query {i+1}/{len(queries)}: {query[:50]}...")
            try:
                results[query] = self.cosine_search(query, top_k=top_k, threshold=threshold)
            except Exception as e:
                logger.error(f"Failed to process query '{query}': {e}")
                results[query] = []
        
        return results
    
    def get_model_specific_search_config(self) -> Dict[str, Any]:
        """
        Get model-specific search configuration and recommendations.
        
        Returns:
            Dictionary with model-specific search settings
        """
        model_id = self.embedding_model.MODEL_ID
        
        config = {
            "model_id": model_id,
            "model_name": self.embedding_model.MODEL_NAME,
            "max_seq_length": self.embedding_model.MAX_SEQ_LENGTH,
            "recommended_top_k": 5,
            "recommended_threshold": 0.0,
            "supports_batch": True,
            "similarity_metric": "cosine"
        }
        
        # Model-specific recommendations
        if model_id == "jina4":
            config.update({
                "recommended_top_k": 10,
                "recommended_threshold": 0.3,
                "notes": "Jina4 performs well with longer queries and multilingual content"
            })
        elif model_id == "qwen34b":
            config.update({
                "recommended_top_k": 8,
                "recommended_threshold": 0.25,
                "notes": "Qwen models are good for technical and multilingual content"
            })
        elif model_id == "bgem3":
            config.update({
                "recommended_top_k": 7,
                "recommended_threshold": 0.2,
                "notes": "BGE-M3 is optimized for multilingual and cross-lingual retrieval"
            })
        elif model_id == "nvembedv2":
            config.update({
                "recommended_top_k": 5,
                "recommended_threshold": 0.4,
                "notes": "NVIDIA models work best with English content and may need higher thresholds"
            })
        elif model_id == "openai":
            config.update({
                "recommended_top_k": 10,
                "recommended_threshold": 0.3,
                "notes": "OpenAI embeddings are well-balanced for most use cases"
            })
        
        return config
    
    def search_by_content(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search for nodes by content similarity using embeddings.
        
        Args:
            query: Search query text
            top_k: Number of top results to return
            
        Returns:
            List of search results
        """
        return self.cosine_search(query, top_k=top_k)
    
    def get_similar_nodes(self, node_id: str, top_k: int = 5, exclude_self: bool = True) -> List[Dict[str, Any]]:
        """
        Find nodes similar to a given node using its embedding.
        
        Args:
            node_id: ID of the reference node
            top_k: Number of similar nodes to return
            exclude_self: Whether to exclude the reference node from results
            
        Returns:
            List of similar nodes
        """
        try:
            # Get the reference node
            from bson import ObjectId
            reference_node = self.collection.find_one(
                {"_id": ObjectId(node_id), "embedding": {"$exists": True}},
                {"embedding": 1, "content": 1}
            )
            
            if not reference_node:
                logger.warning(f"Node {node_id} not found or has no embedding")
                return []
            
            # Use the reference node's embedding as query
            reference_embedding = reference_node["embedding"]
            reference_embedding = np.array(reference_embedding).reshape(1, -1)
            
            # Get all other nodes with embeddings
            filter_query = {"embedding": {"$exists": True}}
            if exclude_self:
                filter_query["_id"] = {"$ne": ObjectId(node_id)}
            
            nodes_with_embeddings = list(self.collection.find(
                filter_query,
                {"_id": 1, "embedding": 1, "content": 1, "metadata": 1}
            ))
            
            if not nodes_with_embeddings:
                return []
            
            # Extract embeddings and calculate similarities
            node_embeddings = []
            node_data = []
            
            for node in nodes_with_embeddings:
                embedding = node.get("embedding")
                if embedding and len(embedding) > 0:
                    node_embeddings.append(embedding)
                    node_data.append({
                        "_id": str(node["_id"]),
                        "content": node.get("content", ""),
                        "metadata": node.get("metadata", {})
                    })
            
            if not node_embeddings:
                return []
            
            node_embeddings = np.array(node_embeddings)
            similarities = cosine_similarity(reference_embedding, node_embeddings)[0]
            
            # Create and sort results
            scored_results = []
            for node, score in zip(node_data, similarities):
                scored_results.append({
                    "_id": node["_id"],
                    "content": node["content"],
                    "metadata": node["metadata"],
                    "score": float(score)
                })
            
            scored_results.sort(key=lambda x: x["score"], reverse=True)
            return scored_results[:top_k]
            
        except Exception as e:
            logger.exception(f"Error finding similar nodes: {e}")
            raise
