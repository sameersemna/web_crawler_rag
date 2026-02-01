#!/bin/bash
# Balanced Start - Good crawling performance with resource control
# Use this when you want the crawler to actually fetch multiple pages

echo "=========================================="
echo "Starting with BALANCED crawling settings"
echo "=========================================="

# Thread limits for stability
export OMP_NUM_THREADS=2
export OPENBLAS_NUM_THREADS=2
export MKL_NUM_THREADS=2
export VECLIB_MAXIMUM_THREADS=2
export NUMEXPR_NUM_THREADS=2
export TOKENIZERS_PARALLELISM=false

# BALANCED crawling settings - more pages, controlled resources
export MAX_WORKERS=1
export CRAWLER_CONCURRENT_REQUESTS=4     # 4 pages simultaneously
export CRAWLER_MAX_THREADS=4
export CRAWLER_DOWNLOAD_DELAY=1          # 1 sec delay (not 2)
export MAX_CRAWL_DEPTH=5                 # Crawl 5 levels deep
export MAX_EMBEDDING_BATCH_SIZE=32
export CHROMADB_MAX_BATCH_SIZE=100
export CHUNK_SIZE=500
export ENABLE_BACKGROUND_CRAWLING=False

echo "✓ Balanced settings configured"
echo "  - Max depth: 5 levels"
echo "  - Concurrent requests: 4"
echo "  - This will crawl more pages per domain"

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

# Start with uvicorn
uvicorn main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 1 \
    --limit-concurrency 50 \
    --timeout-keep-alive 30 \
    --log-level info
