#!/usr/bin/env python3
"""
List all domains in the database with their page counts.
Use this to identify which domains to keep/remove.
"""

import sqlite3
import os
from urllib.parse import urlparse
from collections import Counter

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
    print("Searched:")
    for path in possible_paths:
        print(f"  - {os.path.abspath(path)}")
    return None

def list_domains():
    db_path = find_database()
    if not db_path:
        return
    
    print(f"Using database: {os.path.abspath(db_path)}\n")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    
    if 'crawled_pages' not in tables:
        print(f"ERROR: Table 'crawled_pages' not found in database")
        print(f"Available tables: {', '.join(tables)}")
        conn.close()
        return
    
    # Get all crawled pages
    cursor.execute("SELECT url FROM crawled_pages")
    urls = cursor.fetchall()
    
    # Extract domains
    domains = []
    for (url,) in urls:
        parsed = urlparse(url)
        domain = parsed.netloc
        domains.append(domain)
    
    # Count pages per domain
    domain_counts = Counter(domains)
    
    print(f"\n{'='*60}")
    print(f"DOMAINS IN DATABASE")
    print(f"{'='*60}\n")
    print(f"{'Domain':<40} {'Pages':>10}")
    print(f"{'-'*40} {'-'*10}")
    
    total_pages = 0
    for domain, count in sorted(domain_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"{domain:<40} {count:>10}")
        total_pages += count
    
    print(f"{'-'*40} {'-'*10}")
    print(f"{'TOTAL':<40} {total_pages:>10}")
    print(f"\n{'='*60}\n")
    
    # Get embedding count
    cursor.execute("SELECT COUNT(*) FROM vector_embeddings")
    embedding_count = cursor.fetchone()[0]
    
    print(f"Total pages: {total_pages}")
    print(f"Total embeddings: {embedding_count}")
    print(f"Embeddings per page: {embedding_count/total_pages:.1f} (average)\n")
    
    conn.close()

if __name__ == "__main__":
    list_domains()
