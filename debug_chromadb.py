#!/usr/bin/env python3
"""
Debug ChromaDB collection issues
"""
import chromadb
from pathlib import Path

db_path = Path("./data/vector_db")

print("Connecting to ChromaDB...")
client = chromadb.PersistentClient(path=str(db_path))

print("\nCollections:")
collections = client.list_collections()
for coll in collections:
    print(f"  - {coll.name}")
    
print("\nCollection details:")
collection = client.get_or_create_collection(name="web_crawler_docs")
count = collection.count()
print(f"  Total documents: {count}")

if count > 0:
    print("\nSample query test...")
    try:
        results = collection.query(
            query_embeddings=[[0.1] * 384],  # Dummy embedding
            n_results=1
        )
        print(f"  ✓ Query successful, returned {len(results['ids'][0])} results")
    except Exception as e:
        print(f"  ✗ Query failed: {e}")

    print("\nChecking for data integrity...")
    try:
        # Peek at some documents
        sample = collection.peek(limit=5)
        print(f"  ✓ Sample peek successful, {len(sample['ids'])} docs")
    except Exception as e:
        print(f"  ✗ Peek failed: {e}")

print("\nDone!")
