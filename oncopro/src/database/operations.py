"""
Database operations for managing nodes and embeddings.
"""
import logging
from typing import Iterator, Optional, List, Dict, Any
from pymongo.collection import Collection
from pymongo.cursor import Cursor

from .client import MongoDBClient
from .models import NodeDocument


logger = logging.getLogger(__name__)


class NodesManager:
    """Manager class for node operations in MongoDB."""
    
    def __init__(self, client: Optional[MongoDBClient] = None, collection_name: str = "nodes"):
        """
        Initialize NodesManager.
        
        Args:
            client: MongoDBClient instance. If None, creates a new one.
            collection_name: Name of the nodes collection
        """
        self.client = client or MongoDBClient()
        self.collection_name = collection_name
        self._collection: Optional[Collection] = None
    
    @property
    def collection(self) -> Collection:
        """Get the nodes collection."""
        if self._collection is None:
            self._collection = self.client.get_collection(self.collection_name)
        return self._collection
    
    def count_nodes_without_embeddings(self) -> int:
        """
        Count nodes that don't have embeddings.
        
        Returns:
            Number of nodes without embeddings
        """
        filter_query = {"embedding": {"$exists": False}}
        count = self.collection.count_documents(filter_query)
        logger.info(f"Found {count} nodes without embeddings")
        return count
    
    def find_nodes_without_embeddings(self, batch_size: Optional[int] = None) -> Iterator[NodeDocument]:
        """
        Find all nodes that don't have embeddings.
        
        Args:
            batch_size: Number of documents to retrieve in each batch
            
        Yields:
            NodeDocument instances without embeddings
        """
        filter_query = {"embedding": {"$exists": False}}
        cursor = self.collection.find(filter_query)
        
        if batch_size:
            cursor = cursor.batch_size(batch_size)
        
        for doc in cursor:
            yield NodeDocument.from_dict(doc)
    
    def update_node_embedding(self, node_id: Any, embedding: List[float]) -> bool:
        """
        Update a node with its embedding.
        
        Args:
            node_id: The _id of the node to update
            embedding: The embedding vector
            
        Returns:
            True if update was successful, False otherwise
        """
        try:
            result = self.collection.update_one(
                {"_id": node_id},
                {"$set": {"embedding": embedding}}
            )
            
            if result.modified_count == 1:
                logger.debug(f"Successfully updated embedding for node {node_id}")
                return True
            else:
                logger.warning(f"No document was modified for node {node_id}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to update embedding for node {node_id}: {e}")
            return False
    
    def batch_update_embeddings(self, updates: List[Dict[str, Any]]) -> int:
        """
        Update multiple nodes with their embeddings in a batch operation.
        
        Args:
            updates: List of dictionaries with 'node_id' and 'embedding' keys
            
        Returns:
            Number of successfully updated nodes
        """
        if not updates:
            return 0
        
        try:
            from pymongo import UpdateOne
            
            operations = [
                UpdateOne(
                    {"_id": update["node_id"]},
                    {"$set": {"embedding": update["embedding"]}}
                )
                for update in updates
            ]
            
            result = self.collection.bulk_write(operations)
            updated_count = result.modified_count
            
            logger.info(f"Batch updated {updated_count} nodes with embeddings")
            return updated_count
            
        except Exception as e:
            logger.error(f"Failed to batch update embeddings: {e}")
            return 0
    
    def get_node_by_id(self, node_id: Any) -> Optional[NodeDocument]:
        """
        Get a node by its ID.
        
        Args:
            node_id: The _id of the node
            
        Returns:
            NodeDocument if found, None otherwise
        """
        doc = self.collection.find_one({"_id": node_id})
        if doc:
            return NodeDocument.from_dict(doc)
        return None
    
    def count_all_nodes(self) -> int:
        """
        Count total number of nodes in the collection.
        
        Returns:
            Total number of nodes
        """
        return self.collection.count_documents({})
    
    def count_nodes_with_embeddings(self) -> int:
        """
        Count nodes that have embeddings.
        
        Returns:
            Number of nodes with embeddings
        """
        filter_query = {"embedding": {"$exists": True}}
        return self.collection.count_documents(filter_query)
    
    def get_collection_stats(self) -> Dict[str, int]:
        """
        Get statistics about the nodes collection.
        
        Returns:
            Dictionary with collection statistics
        """
        total_nodes = self.count_all_nodes()
        nodes_with_embeddings = self.count_nodes_with_embeddings()
        nodes_without_embeddings = total_nodes - nodes_with_embeddings
        
        return {
            "total_nodes": total_nodes,
            "nodes_with_embeddings": nodes_with_embeddings,
            "nodes_without_embeddings": nodes_without_embeddings,
            "embedding_completion_percentage": (
                (nodes_with_embeddings / total_nodes * 100) if total_nodes > 0 else 0
            )
        }
