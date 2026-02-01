#!/bin/bash
# Balanced Start - Good crawling performance with resource control
# Use this when you want the crawler to actually fetch multiple pages

echo "=========================================="
echo "Starting with BALANCED crawling settings"
echo "=========================================="

# Increased thread limits for large collection queries
export OMP_NUM_THREADS=4
export OPENBLAS_NUM_THREADS=4
export MKL_NUM_THREADS=4
export VECLIB_MAXIMUM_THREADS=4
export NUMEXPR_NUM_THREADS=4
export TOKENIZERS_PARALLELISM=false

# BALANCED settings - good for 30k+ document collections
export MAX_WORKERS=2                     # 2 workers for better stability
export CRAWLER_CONCURRENT_REQUESTS=4     # 4 pages simultaneously
export CRAWLER_MAX_THREADS=4
export CRAWLER_DOWNLOAD_DELAY=1          # 1 sec delay (not 2)
export MAX_CRAWL_DEPTH=5                 # Crawl 5 levels deep
export MAX_EMBEDDING_BATCH_SIZE=32
export CHROMADB_MAX_BATCH_SIZE=100
export CHUNK_SIZE=500
export ENABLE_BACKGROUND_CRAWLING=False

# CRITICAL: Reduce query load for large collections
export RAG_TOP_K_RESULTS=3               # Fewer results = less memory

echo "✓ Balanced settings configured for large collections"
echo "  - Threads: 4 (increased for query performance)"
echo "  - Workers: 2"
echo "  - Max depth: 5 levels"
echo "  - Top K results: 3 (reduced for large collections)"
echo "  - This should handle 30k+ document queries"

# Activate venv if needed
if [ -z "$VIRTUAL_ENV" ]; then
    if [ -d "venv" ]; then
        echo ""
        echo "Activating virtual environment..."
        source venv/bin/activate
    fi
fi

echo ""
echo "=========================================="
echo "Starting application..."
echo "=========================================="
echo ""

# Start with uvicorn (increased workers for large collections)
uvicorn main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 2 \
    --limit-concurrency 50 \
    --timeout-keep-alive 30 \
    --log-level info
