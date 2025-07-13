#!/usr/bin/env python3
"""
Test script for the database module functionality.
"""

from src import (
    MongoDBClient,
    NodesManager, 
    NodeDocument,
    setup_logging
)


def test_database_connection():
    """Test basic database connection."""
    print("Testing database connection...")
    
    try:
        with MongoDBClient() as client:
            # Test connection
            client.connect()
            
            # Test database access
            db = client.get_database()
            print(f"✅ Connected to database: {db.name}")
            
            # Test collection access
            collection = client.get_collection("nodes")
            print(f"✅ Accessed collection: {collection.name}")
            
            return True
            
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False


def test_nodes_manager():
    """Test NodesManager functionality."""
    print("\nTesting NodesManager...")
    
    try:
        with MongoDBClient() as client:
            manager = NodesManager(client)
            
            # Test statistics
            stats = manager.get_collection_stats()
            print(f"✅ Collection stats: {stats}")
            
            # Test counting operations
            total = manager.count_all_nodes()
            with_embeddings = manager.count_nodes_with_embeddings()
            without_embeddings = manager.count_nodes_without_embeddings()
            
            print(f"   Total nodes: {total}")
            print(f"   With embeddings: {with_embeddings}")
            print(f"   Without embeddings: {without_embeddings}")
            
            return True
            
    except Exception as e:
        print(f"❌ NodesManager test failed: {e}")
        return False


def test_node_document():
    """Test NodeDocument model."""
    print("\nTesting NodeDocument model...")
    
    try:
        # Test document creation
        test_data = {
            "_id": "test_id",
            "text": "Test title",
            "richText": "Test description",
            "notes": "Test notes",
            "links": ["http://example.com"],
            "attributes": [{"name": "test", "value": "value"}]
        }
        
        node = NodeDocument.from_dict(test_data)
        print(f"✅ Created NodeDocument: {node._id}")
        
        # Test text generation
        text_content = node.generate_text_content()
        print(f"✅ Generated text content: {text_content[:100]}...")
        
        # Test embedding check
        has_embedding = node.has_embedding()
        print(f"✅ Has embedding check: {has_embedding}")
        
        return True
        
    except Exception as e:
        print(f"❌ NodeDocument test failed: {e}")
        return False


def main():
    """Run all tests."""
    setup_logging()
    
    print("=== Database Module Tests ===\n")
    
    tests = [
        test_database_connection,
        test_nodes_manager,
        test_node_document
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print(f"\n=== Test Results ===")
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed!")
    else:
        print("⚠️  Some tests failed")


if __name__ == "__main__":
    main()
