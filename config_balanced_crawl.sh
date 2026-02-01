# Balanced Crawling Configuration
# Use this for effective crawling while keeping resource usage reasonable

# Copy these to your .env file or export before starting

# BALANCED MODE - Good crawling performance with controlled resources
export MAX_CRAWL_DEPTH=5              # Crawl up to 5 levels deep
export CRAWLER_CONCURRENT_REQUESTS=4  # 4 pages at once (balanced)
export CRAWLER_DOWNLOAD_DELAY=1       # 1 second between batches
export CRAWLER_MAX_THREADS=4          # Allow 4 download threads
export MAX_EMBEDDING_BATCH_SIZE=32    # Process 32 chunks at a time
export CHROMADB_MAX_BATCH_SIZE=100    # Database batch size
export CHUNK_SIZE=500                 # Smaller chunks = more data points
export ENABLE_BACKGROUND_CRAWLING=False  # Still manual control

# Thread limits (keep conservative for stability)
export OMP_NUM_THREADS=2
export OPENBLAS_NUM_THREADS=2
export MKL_NUM_THREADS=2

# Workers
export MAX_WORKERS=1

echo "Balanced crawling configuration loaded"
echo "This will crawl more pages while keeping resource usage reasonable"
