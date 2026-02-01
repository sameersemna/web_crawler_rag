#!/usr/bin/env python3
"""
Check database for crawled pages
"""
import sqlite3

db_path = "./data/crawler_rag.db"

print("Connecting to database...")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("\nTables:")
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
for table in tables:
    print(f"  - {table[0]}")

print("\nCrawled pages:")
cursor.execute("SELECT COUNT(*) FROM crawled_pages")
count = cursor.fetchone()[0]
print(f"  Total: {count}")

if count > 0:
    cursor.execute("SELECT domain, url, content_type, LENGTH(content) as content_len FROM crawled_pages LIMIT 5")
    pages = cursor.fetchall()
    print("\n  Sample pages:")
    for domain, url, ctype, clen in pages:
        print(f"    - {domain}: {url[:60]} ({ctype}, {clen} chars)")

print("\nVector embeddings:")
cursor.execute("SELECT COUNT(*) FROM vector_embeddings")
count = cursor.fetchone()[0]
print(f"  Total: {count}")

if count > 0:
    # Get column names first
    cursor.execute("PRAGMA table_info(vector_embeddings)")
    columns = [col[1] for col in cursor.fetchall()]
    print(f"  Columns: {columns}")
    
    cursor.execute("SELECT * FROM vector_embeddings LIMIT 3")
    embeddings = cursor.fetchall()
    print(f"\n  Sample embeddings (first 3):")
    for row in embeddings:
        print(f"    - {row}")

conn.close()
print("\nDone!")
