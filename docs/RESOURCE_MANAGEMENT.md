# Resource Management Guide

This document explains the resource limiting configurations added to prevent system hangs and crashes.

## Overview

The web crawler RAG application can be resource-intensive, especially when:
- Crawling multiple websites simultaneously
- Processing large documents and PDFs
- Generating embeddings for vector database
- Running ML models (sentence transformers)

To prevent system resource exhaustion, comprehensive limits have been implemented at multiple levels.

## Docker Resource Limits

### CPU Limits
The application is limited to **4 CPU cores** maximum:

```yaml
deploy:
  resources:
    limits:
      cpus: '4.0'
      memory: 4G
    reservations:
      cpus: '1.0'
      memory: 512M
```

### Memory Limits
- **Maximum**: 4GB RAM
- **Reserved**: 512MB minimum

## Environment Variables for Resource Control

### 1. Application Workers

**MAX_WORKERS=2**
- Controls the number of Uvicorn worker processes
- Recommended: 2-4 workers for 4-core systems
- Lower value = less memory usage, slightly lower throughput

### 2. Thread Limiting Variables

These environment variables limit the number of threads used by numerical libraries:

```bash
OMP_NUM_THREADS=4          # OpenMP threads
OPENBLAS_NUM_THREADS=4     # OpenBLAS linear algebra
MKL_NUM_THREADS=4          # Intel MKL
VECLIB_MAXIMUM_THREADS=4   # Apple Accelerate framework
NUMEXPR_NUM_THREADS=4      # NumExpr evaluation
```

**Why this matters**: Libraries like NumPy, SciPy, and sentence-transformers use these to determine parallelism. Without limits, they may spawn threads equal to total CPU count, causing contention.

### 3. Crawler Resource Limits

**CRAWLER_CONCURRENT_REQUESTS=4**
- Reduced from 16 to limit simultaneous HTTP requests
- Lower value = less network/memory pressure
- Adjustable based on your system capacity

**CRAWLER_MAX_THREADS=4**
- Limits concurrent download threads
- Prevents excessive thread creation during crawling

**CRAWLER_TIMEOUT=30**
- 30-second timeout per request
- Prevents hanging on slow/unresponsive websites

### 4. Vector Database Limits

**MAX_EMBEDDING_BATCH_SIZE=32**
- Process embeddings in batches of 32 chunks
- Prevents memory spikes when encoding large documents
- Lower value = slower but more stable

**CHROMADB_MAX_BATCH_SIZE=100**
- Limits ChromaDB batch insert operations
- Prevents database lock contention and memory issues

## Configuration Tiers

### Conservative (Recommended for systems with frequent crashes)

```bash
MAX_WORKERS=1
CRAWLER_CONCURRENT_REQUESTS=2
CRAWLER_MAX_THREADS=2
MAX_EMBEDDING_BATCH_SIZE=16
CHROMADB_MAX_BATCH_SIZE=50
OMP_NUM_THREADS=2
```

Docker limits:
```yaml
cpus: '2.0'
memory: 2G
```

### Balanced (Current default - good for most systems)

```bash
MAX_WORKERS=2
CRAWLER_CONCURRENT_REQUESTS=4
CRAWLER_MAX_THREADS=4
MAX_EMBEDDING_BATCH_SIZE=32
CHROMADB_MAX_BATCH_SIZE=100
OMP_NUM_THREADS=4
```

Docker limits:
```yaml
cpus: '4.0'
memory: 4G
```

### Aggressive (For powerful systems with 8+ cores)

```bash
MAX_WORKERS=4
CRAWLER_CONCURRENT_REQUESTS=8
CRAWLER_MAX_THREADS=8
MAX_EMBEDDING_BATCH_SIZE=64
CHROMADB_MAX_BATCH_SIZE=200
OMP_NUM_THREADS=8
```

Docker limits:
```yaml
cpus: '8.0'
memory: 8G
```

## Additional Optimizations

### 1. Disable Background Crawling

If you're experiencing issues, temporarily disable automatic crawling:

```bash
ENABLE_BACKGROUND_CRAWLING=False
```

Then manually trigger crawls when system resources are available.

### 2. Reduce Crawl Depth

Limit how deep the crawler goes:

```bash
MAX_CRAWL_DEPTH=2  # Default is 5
```

### 3. Increase Download Delay

Add more delay between requests to reduce load:

```bash
CRAWLER_DOWNLOAD_DELAY=2  # Default is 1 second
```

### 4. Disable OCR for PDFs

If not needed, disable resource-intensive OCR:

```bash
ENABLE_OCR=False
```

### 5. Limit PDF Pages

Prevent processing of very large PDFs:

```bash
PDF_MAX_PAGES=100  # Default is 500
```

## Monitoring Resource Usage

### Check Docker Container Resources

```bash
# Real-time stats
docker stats web_crawler_rag_api

# Detailed inspection
docker inspect web_crawler_rag_api | jq '.[0].HostConfig.NanoCpus'
```

### Check Application Logs

Monitor for resource-related warnings:

```bash
tail -f data/logs/crawler.log | grep -i "memory\|timeout\|error"
```

### System Resource Monitoring

```bash
# CPU usage
htop

# Memory usage
free -h

# Process tree
pstree -p $(docker inspect -f '{{.State.Pid}}' web_crawler_rag_api)
```

## Troubleshooting

### System Still Hangs

1. **Reduce MAX_WORKERS to 1**
2. **Lower CRAWLER_CONCURRENT_REQUESTS to 2**
3. **Reduce Docker CPU limit to 2.0**
4. **Disable background crawling**

### Out of Memory Errors

1. **Reduce MAX_EMBEDDING_BATCH_SIZE to 16**
2. **Lower CHROMADB_MAX_BATCH_SIZE to 50**
3. **Increase Docker memory limit if possible**
4. **Enable swap space on host system**

### VS Code Crashes

The Docker limits will prevent the container from consuming excessive resources. However:

1. **Check VS Code extensions** - Some extensions are resource-intensive
2. **Increase VS Code memory limit**: Add to settings.json:
   ```json
   "files.maxMemoryForLargeFilesMB": 4096
   ```
3. **Close unnecessary editor tabs**
4. **Disable unused VS Code extensions**

### Slow Performance

Resource limits will reduce performance. Balance based on your needs:

- **For faster crawling**: Increase `CRAWLER_CONCURRENT_REQUESTS`
- **For faster embeddings**: Increase `MAX_EMBEDDING_BATCH_SIZE`
- **For more throughput**: Increase `MAX_WORKERS`

But monitor system stability when increasing these values.

## Applying Changes

After modifying environment variables:

```bash
# Rebuild and restart
docker-compose down
docker-compose build
docker-compose up -d

# Check logs
docker-compose logs -f
```

## Best Practices

1. **Start conservative** - Use lower limits and gradually increase
2. **Monitor during crawls** - Watch resource usage during active crawling
3. **Test with single domain** - Validate settings before crawling multiple sites
4. **Set up alerting** - Use system monitoring tools for early warning
5. **Regular restarts** - Consider periodic container restarts to free resources

## Summary of Changes Made

1. ✅ Added Docker CPU limit: 4 cores
2. ✅ Added Docker memory limit: 4GB
3. ✅ Reduced concurrent requests: 16 → 4
4. ✅ Added thread limiting environment variables
5. ✅ Added embedding batch size limits
6. ✅ Updated crawler connector limits
7. ✅ Implemented batch processing in vector database
8. ✅ Added Uvicorn concurrency limits

These changes should significantly reduce the risk of system hangs and crashes.
