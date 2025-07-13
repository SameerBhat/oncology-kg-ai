"""
MongoDB client configuration and connection management.
"""
import logging
from typing import Optional
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection

from ..config.settings import MONGO_URI, DATABASE_NAME


logger = logging.getLogger(__name__)


class MongoDBClient:
    """MongoDB client wrapper for connection management."""
    
    def __init__(self, uri: Optional[str] = None, database_name: Optional[str] = None):
        """
        Initialize MongoDB client.
        
        Args:
            uri: MongoDB connection URI. Defaults to settings.MONGO_URI
            database_name: Database name. Defaults to settings.DATABASE_NAME
        """
        self.uri = uri or MONGO_URI
        self.database_name = database_name or DATABASE_NAME
        self._client: Optional[MongoClient] = None
        self._database: Optional[Database] = None
        
    def connect(self) -> MongoClient:
        """
        Establish connection to MongoDB.
        
        Returns:
            MongoClient instance
        """
        if self._client is None:
            logger.info(f"Connecting to MongoDB at {self.uri}")
            self._client = MongoClient(self.uri)
            
            # Test connection
            try:
                self._client.admin.command('ping')
                logger.info("Successfully connected to MongoDB")
            except Exception as e:
                logger.error(f"Failed to connect to MongoDB: {e}")
                raise
                
        return self._client
    
    def get_database(self) -> Database:
        """
        Get database instance.
        
        Returns:
            Database instance
        """
        if self._database is None:
            client = self.connect()
            self._database = client[self.database_name]
            logger.info(f"Using database: {self.database_name}")
            
        return self._database
    
    def get_collection(self, collection_name: str) -> Collection:
        """
        Get collection instance.
        
        Args:
            collection_name: Name of the collection
            
        Returns:
            Collection instance
        """
        database = self.get_database()
        return database[collection_name]
    
    def close(self) -> None:
        """Close the MongoDB connection."""
        if self._client:
            self._client.close()
            self._client = None
            self._database = None
            logger.info("MongoDB connection closed")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
