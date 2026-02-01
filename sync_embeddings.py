#!/usr/bin/env python3
"""
Sync embeddings from SQLite to ChromaDB
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db_context
from app.models.database import CrawledPage
from app.services.vector_db import vector_db
from app.core.logging import app_logger

def sync_embeddings():
    """Sync all crawled pages to ChromaDB"""
    
    print("=" * 60)
    print("Syncing Embeddings from SQLite to ChromaDB")
    print("=" * 60)
    
    # Initialize vector DB
    print("\nInitializing vector database...")
    if not vector_db._initialized:
        vector_db._initialize()
    
    # Get all crawled pages
    print("\nFetching crawled pages from SQLite...")
    with get_db_context() as db:
        pages = db.query(CrawledPage).all()
        total_pages = len(pages)
        
        print(f"Found {total_pages} pages in SQLite")
        
        if total_pages == 0:
            print("No pages to sync!")
            return
        
        # Check current ChromaDB count
        current_count = vector_db.collection.count()
        print(f"Current ChromaDB documents: {current_count}")
        
        # Add documents to ChromaDB
        print(f"\nAdding {total_pages} pages to ChromaDB...")
        print("This may take a while...")
        
        try:
            vector_db.add_documents(pages)
            
            # Verify
            new_count = vector_db.collection.count()
            print(f"\n✓ Sync complete!")
            print(f"  ChromaDB documents: {current_count} → {new_count}")
            print(f"  Added: {new_count - current_count}")
            
        except Exception as e:
            print(f"\n✗ Sync failed: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    sync_embeddings()
