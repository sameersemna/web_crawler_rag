#!/usr/bin/env python3
"""
Clean up database by removing specific domains.
This reduces the collection size for better query performance.

Usage:
    python cleanup_domains.py domain1.com domain2.com
"""

import sys
import sqlite3
import os
from urllib.parse import urlparse

def find_database():
    """Find the database file"""
    possible_paths = [
        'data/crawler_rag.db',
        'data/web_crawler.db',
        'crawler_rag.db',
        'web_crawler.db',
        '../data/crawler_rag.db',
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    print("ERROR: Could not find database file")
    return None

def cleanup_domains(domains_to_remove):
    if not domains_to_remove:
        print("Usage: python cleanup_domains.py domain1.com domain2.com ...")
        print("\nRun 'python list_domains.py' first to see available domains")
        return
    
    db_path = find_database()
    if not db_path:
        return
    db_path = find_database()
    if not db_path:
        return
    
    print(f"\n{'='*60}")
    print(f"DOMAIN CLEANUP")
    print(f"{'='*60}\n")
    print(f"Database: {os.path.abspath(db_path)}")
    print(f"Domains to remove: {', '.join(domains_to_remove)}\n")
    
    response = input("This will DELETE all pages and embeddings for these domains. Continue? (yes/no): ")
    if response.lower() != 'yes':
        print("Cancelled.")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    total_pages_deleted = 0
    total_embeddings_deleted = 0
    
    for domain in domains_to_remove:
        # Find pages matching this domain
        cursor.execute("""
            SELECT id, url FROM crawled_pages 
            WHERE url LIKE ?
        """, (f'%{domain}%',))
        
        pages = cursor.fetchall()
        page_ids = [p[0] for p in pages]
        
        if not page_ids:
            print(f"✗ No pages found for domain: {domain}")
            continue
        
        print(f"\nProcessing domain: {domain}")
        print(f"  Pages found: {len(page_ids)}")
        
        # Delete embeddings for these pages
        placeholders = ','.join('?' * len(page_ids))
        cursor.execute(f"""
            DELETE FROM vector_embeddings 
            WHERE page_id IN ({placeholders})
        """, page_ids)
        embeddings_deleted = cursor.rowcount
        
        # Delete the pages
        cursor.execute(f"""
            DELETE FROM crawled_pages 
            WHERE id IN ({placeholders})
        """, page_ids)
        pages_deleted = cursor.rowcount
        
        total_pages_deleted += pages_deleted
        total_embeddings_deleted += embeddings_deleted
        
        print(f"  ✓ Deleted {pages_deleted} pages")
        print(f"  ✓ Deleted {embeddings_deleted} embeddings")
    
    conn.commit()
    
    # Get final counts
    cursor.execute("SELECT COUNT(*) FROM crawled_pages")
    remaining_pages = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM vector_embeddings")
    remaining_embeddings = cursor.fetchone()[0]
    
    conn.close()
    
    print(f"\n{'='*60}")
    print(f"CLEANUP COMPLETE")
    print(f"{'='*60}\n")
    print(f"Deleted: {total_pages_deleted} pages, {total_embeddings_deleted} embeddings")
    print(f"Remaining: {remaining_pages} pages, {remaining_embeddings} embeddings")
    print(f"\n⚠️  IMPORTANT: You must reset ChromaDB to sync the changes!")
    print(f"Run: rm -rf data/vector_db/* && python sync_embeddings.py\n")

if __name__ == "__main__":
    domains_to_remove = sys.argv[1:]
    cleanup_domains(domains_to_remove)
