#!/bin/bash
# Safe Start Script with Resource Limits
# This script applies OS-level resource limits before starting the application

echo "=========================================="
echo "Starting Web Crawler RAG with Resource Limits"
echo "=========================================="

# Set environment variables for thread control
export OMP_NUM_THREADS=2
export OPENBLAS_NUM_THREADS=2
export MKL_NUM_THREADS=2
export VECLIB_MAXIMUM_THREADS=2
export NUMEXPR_NUM_THREADS=2
export TOKENIZERS_PARALLELISM=false

# Conservative application settings
export MAX_WORKERS=1
export CRAWLER_CONCURRENT_REQUESTS=2
export CRAWLER_MAX_THREADS=2
export MAX_EMBEDDING_BATCH_SIZE=16
export CHROMADB_MAX_BATCH_SIZE=50
export ENABLE_BACKGROUND_CRAWLING=False

echo "✓ Environment variables set"
echo "  - Thread limit: 2"
echo "  - Concurrent requests: 2"
echo "  - Background crawling: Disabled"

# Try to set process limits (requires no special permissions)
echo ""
echo "Applying process limits..."

# NOTE: Some limits removed as they prevent application startup
# Virtual memory limit removed (too restrictive for Python/ML models)
# ulimit -v 4194304 

# Process limit removed (Python needs more processes to fork)
# ulimit -u 256

# Limit stack size to 8MB
ulimit -s 8192 2>/dev/null && echo "✓ Stack size limited to 8MB" || echo "⚠ Could not set stack limit"

# Limit number of open files
ulimit -n 1024 2>/dev/null && echo "✓ Open files limited to 1024" || echo "⚠ Could not set file limit"

# Limit CPU time per process to 3600 seconds (1 hour)
ulimit -t 3600 2>/dev/null && echo "✓ CPU time limited to 1 hour per process" || echo "⚠ Could not set CPU time limit"

echo "✓ Resource limits applied (memory/process limits skipped to allow startup)"

echo ""
echo "=========================================="
echo "Starting application with Uvicorn..."
echo "=========================================="
echo ""

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    if [ -d "venv" ]; then
        echo "Activating virtual environment..."
        source venv/bin/activate
    else
        echo "⚠ Warning: Virtual environment not found or activated"
    fi
fi

# Start the application with conservative settings
# --workers 1: Single worker process to minimize resource usage
# --limit-concurrency 20: Limit concurrent connections
# --timeout-keep-alive 30: Close idle connections quickly
# --backlog 50: Limit pending connections
uvicorn main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 1 \
    --limit-concurrency 20 \
    --timeout-keep-alive 30 \
    --backlog 50 \
    --log-level info

# If uvicorn fails, try with python directly
if [ $? -ne 0 ]; then
    echo ""
    echo "Uvicorn failed, trying with python directly..."
    python main.py
fi
