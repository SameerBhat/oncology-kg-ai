"""
Database operations for managing nodes and embeddings.
"""
import logging
from typing import Iterator, Optional, List, Dict, Any, Union
from pymongo.collection import Collection
from pymongo.cursor import Cursor
from bson import ObjectId

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


class QuestionsManager:
    """Manager class for question operations in MongoDB."""
    
    def __init__(self, client: Optional[MongoDBClient] = None, collection_name: str = "questions"):
        """
        Initialize QuestionsManager.
        
        Args:
            client: MongoDBClient instance. If None, creates a new one with "oncopro" database.
            collection_name: Name of the questions collection
        """
        if client is None:
            # Create a new client with the "oncopro" database
            self.client = MongoDBClient(database_name="oncopro")
        else:
            # Use the provided client (assumes it's already configured for the right database)
            self.client = client
        
        self.collection_name = collection_name
        self._collection: Optional[Collection] = None
    
    @property
    def collection(self) -> Collection:
        """Get the questions collection."""
        if self._collection is None:
            self._collection = self.client.get_collection(self.collection_name)
        return self._collection
    
    def insert_question(self, question_en: str, question_de: str) -> Any:
        """
        Insert a single question into the collection.
        
        Args:
            question_en: English question text
            question_de: German question text
            
        Returns:
            Inserted document ID
        """
        document = {
            "question_en": question_en,
            "question_de": question_de
        }
        
        result = self.collection.insert_one(document)
        logger.info(f"Inserted question with ID: {result.inserted_id}")
        return result.inserted_id
    
    def insert_questions_batch(self, questions: List[Dict[str, str]]) -> List[Any]:
        """
        Insert multiple questions into the collection.
        
        Args:
            questions: List of dictionaries with 'question_en' and 'question_de' keys
            
        Returns:
            List of inserted document IDs
        """
        if not questions:
            logger.warning("No questions to insert")
            return []
        
        result = self.collection.insert_many(questions)
        logger.info(f"Inserted {len(result.inserted_ids)} questions")
        return result.inserted_ids
    
    def count_questions(self) -> int:
        """
        Count total number of questions in the collection.
        
        Returns:
            Total number of questions
        """
        return self.collection.count_documents({})
    
    def clear_all_questions(self) -> int:
        """
        Clear all questions from the collection.
        
        Returns:
            Number of questions deleted
        """
        result = self.collection.delete_many({})
        logger.info(f"Deleted {result.deleted_count} questions from collection")
        return result.deleted_count
    
    def get_questions(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Retrieve questions from the collection.
        
        Args:
            limit: Maximum number of questions to retrieve. If None, retrieves all.
            
        Returns:
            List of question documents
        """
        cursor = self.collection.find({})
        if limit:
            cursor = cursor.limit(limit)
        
        return list(cursor)
    
    def question_exists(self, question_en: str, question_de: str) -> bool:
        """
        Check if a question already exists in the collection.
        
        Args:
            question_en: English question text
            question_de: German question text
            
        Returns:
            True if question exists, False otherwise
        """
        query = {
            "$or": [
                {"question_en": question_en, "question_de": question_de},
                {"question_en": question_en},
                {"question_de": question_de}
            ]
        }
        
        return self.collection.count_documents(query) > 0
    
    def get_existing_questions_set(self) -> set:
        """
        Get a set of existing question tuples for efficient duplicate checking.
        
        Returns:
            Set of (question_en, question_de) tuples
        """
        cursor = self.collection.find({}, {"question_en": 1, "question_de": 1})
        return {(doc.get("question_en", ""), doc.get("question_de", "")) for doc in cursor}
    
    def insert_questions_batch_idempotent(self, questions: List[Dict[str, str]]) -> Dict[str, int]:
        """
        Insert multiple questions into the collection, skipping duplicates.
        
        Args:
            questions: List of dictionaries with 'question_en' and 'question_de' keys
            
        Returns:
            Dictionary with counts of inserted, skipped, and total questions
        """
        if not questions:
            logger.warning("No questions to insert")
            return {"inserted": 0, "skipped": 0, "total": 0}
        
        # Get existing questions for efficient comparison
        existing_questions = self.get_existing_questions_set()
        logger.info(f"Found {len(existing_questions)} existing questions in collection")
        
        # Filter out duplicates
        new_questions = []
        skipped_count = 0
        
        for question in questions:
            question_en = question.get('question_en', '')
            question_de = question.get('question_de', '')
            question_tuple = (question_en, question_de)
            
            if question_tuple in existing_questions:
                skipped_count += 1
                logger.debug(f"Skipping duplicate question: EN='{question_en[:50]}...', DE='{question_de[:50]}...'")
            else:
                new_questions.append(question)
                existing_questions.add(question_tuple)  # Add to set to prevent duplicates within the batch
        
        # Insert only new questions
        inserted_count = 0
        if new_questions:
            result = self.collection.insert_many(new_questions)
            inserted_count = len(result.inserted_ids)
            logger.info(f"Inserted {inserted_count} new questions")
        
        if skipped_count > 0:
            logger.info(f"Skipped {skipped_count} duplicate questions")
        
        return {
            "inserted": inserted_count,
            "skipped": skipped_count,
            "total": len(questions)
        }


class AnswersManager:
    """Manager class for answer operations in MongoDB."""
    
    def __init__(self, client: Optional[MongoDBClient] = None, collection_name: str = "answers"):
        """
        Initialize AnswersManager.
        
        Args:
            client: MongoDBClient instance. If None, creates a new one with "oncopro" database.
            collection_name: Name of the answers collection
        """
        if client is None:
            # Create a new client with the "oncopro" database
            self.client = MongoDBClient(database_name="oncopro")
        else:
            # Use the provided client (assumes it's already configured for the right database)
            self.client = client
        
        self.collection_name = collection_name
        self._collection: Optional[Collection] = None
    
    @property
    def collection(self) -> Collection:
        """Get the answers collection."""
        if self._collection is None:
            self._collection = self.client.get_collection(self.collection_name)
        return self._collection
    
    def answer_exists(self, question_id: Union[str, ObjectId], model_name: str) -> bool:
        """
        Check if an answer already exists for a given question and model.
        
        Args:
            question_id: ID of the question (can be string or ObjectId)
            model_name: Name of the embedding model
            
        Returns:
            True if answer exists, False otherwise
        """
        # Convert string to ObjectId if needed
        if isinstance(question_id, str):
            question_id = ObjectId(question_id)
            
        query = {
            "question_id": question_id,
            "model_name": model_name
        }
        
        return self.collection.count_documents(query) > 0
    
    def insert_answer(self, question_id: Union[str, ObjectId], model_name: str, nodes: List[Dict[str, Any]]) -> Any:
        """
        Insert a single answer into the collection.
        
        Args:
            question_id: ID of the question (can be string or ObjectId)
            model_name: Name of the embedding model
            nodes: List of search result nodes
            
        Returns:
            Inserted document ID
        """
        # Convert string to ObjectId if needed
        if isinstance(question_id, str):
            question_id = ObjectId(question_id)
            
        document = {
            "question_id": question_id,
            "model_name": model_name,
            "nodes": nodes,
            "ordered_nodes": [],
            "completed": False
        }
        
        result = self.collection.insert_one(document)
        logger.info(f"Inserted answer with ID: {result.inserted_id}")
        return result.inserted_id
    
    def count_answers(self, model_name: Optional[str] = None) -> int:
        """
        Count total number of answers in the collection.
        
        Args:
            model_name: Optional model name to filter by
            
        Returns:
            Total number of answers
        """
        query = {}
        if model_name:
            query["model_name"] = model_name
        
        return self.collection.count_documents(query)
    
    def get_answers(self, model_name: Optional[str] = None, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Retrieve answers from the collection.
        
        Args:
            model_name: Optional model name to filter by
            limit: Maximum number of answers to retrieve. If None, retrieves all.
            
        Returns:
            List of answer documents
        """
        query = {}
        if model_name:
            query["model_name"] = model_name
            
        cursor = self.collection.find(query)
        if limit:
            cursor = cursor.limit(limit)
        
        return list(cursor)
    
    def clear_answers_by_model(self, model_name: str) -> int:
        """
        Clear all answers for a specific model.
        
        Args:
            model_name: Name of the embedding model
            
        Returns:
            Number of answers deleted
        """
        result = self.collection.delete_many({"model_name": model_name})
        logger.info(f"Deleted {result.deleted_count} answers for model {model_name}")
        return result.deleted_count
    
    def get_answers_stats(self) -> Dict[str, int]:
        """
        Get statistics about answers in the collection.
        
        Returns:
            Dictionary with answer statistics
        """
        pipeline = [
            {
                "$group": {
                    "_id": "$model_name",
                    "count": {"$sum": 1},
                    "completed": {"$sum": {"$cond": [{"$eq": ["$completed", True]}, 1, 0]}}
                }
            }
        ]
        
        results = list(self.collection.aggregate(pipeline))
        
        stats = {
            "total_answers": self.collection.count_documents({}),
            "by_model": {result["_id"]: {"count": result["count"], "completed": result["completed"]} for result in results}
        }
        
        return stats
