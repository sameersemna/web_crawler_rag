#!/bin/bash
# MINIMAL SAFE MODE - Absolute bare minimum to start server
# Use this if system keeps hanging with start_safe.sh

echo "=========================================="
echo "MINIMAL SAFE MODE"
echo "Starting with ABSOLUTE MINIMUM resources"
echo "=========================================="

# Ultra-conservative thread limits
export OMP_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1
export VECLIB_MAXIMUM_THREADS=1
export NUMEXPR_NUM_THREADS=1
export TOKENIZERS_PARALLELISM=false

# Minimal application settings
export MAX_WORKERS=1
export CRAWLER_CONCURRENT_REQUESTS=1  # Only 1 page at a time
export CRAWLER_MAX_THREADS=1
export MAX_CRAWL_DEPTH=2              # Only 2 levels deep
export MAX_EMBEDDING_BATCH_SIZE=8     # Very small batches
export CHROMADB_MAX_BATCH_SIZE=25
export CHUNK_SIZE=200
export ENABLE_BACKGROUND_CRAWLING=False
export ENABLE_OCR=False

echo "✓ Ultra-conservative limits set"
echo "  - All threads: 1"
echo "  - Concurrent requests: 1"
echo "  - Batch sizes: MINIMAL"
echo "  - OCR: DISABLED"
echo "  - Background crawling: DISABLED"

# Check if venv exists
if [ -z "$VIRTUAL_ENV" ]; then
    if [ -d "venv" ]; then
        echo ""
        echo "Activating virtual environment..."
        source venv/bin/activate
    else
        echo ""
        echo "⚠ WARNING: Virtual environment not found!"
        echo "Press Ctrl+C to cancel, or wait 5 seconds to continue..."
        sleep 5
    fi
fi

echo ""
echo "=========================================="
echo "Starting in MINIMAL mode..."
echo "Heavy ML models will NOT load at startup"
echo "They will only load when first used"
echo "=========================================="
echo ""
sleep 2

# Start with absolute minimal settings
python -u main.py

# If that fails, try uvicorn directly
if [ $? -ne 0 ]; then
    echo ""
    echo "Python failed, trying uvicorn..."
    uvicorn main:app \
        --host 127.0.0.1 \
        --port 8000 \
        --workers 1 \
        --limit-concurrency 5 \
        --timeout-keep-alive 15 \
        --log-level warning
fi
