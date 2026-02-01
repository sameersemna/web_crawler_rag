# Service Architecture

The system is now split into two independent services:

## Services

### 1. API Server (`main.py`)
- **Purpose**: Handles HTTP API requests
- **Features**:
  - Query endpoint for RAG queries
  - Manual crawl trigger endpoint
  - Status, health, stats endpoints
  - Background tasks for API-triggered crawls
- **Starts with**: `./start_api.sh` or `python main.py`
- **Port**: 8000 (default)
- **Independent**: Runs without automatic crawling

### 2. Background Crawler (`main_crawl.py`)
- **Purpose**: Automatic scheduled crawling
- **Features**:
  - Periodic domain crawling (configurable interval)
  - Loads domains from CSV
  - Updates vector database
  - Runs independently from API
- **Starts with**: `./start_crawl.sh` or `python main_crawl.py`
- **Requires**: `ENABLE_BACKGROUND_CRAWLING=True` in `.env`
- **Independent**: Can run without API server

## Start Options

### Option 1: API Only (Recommended for testing)
```bash
./start_api.sh
# or
./start_minimal.sh  # Even safer with minimal resources
```
**Use when**: You want to test API features or manually trigger crawls

### Option 2: Background Crawler Only
```bash
./start_crawl.sh
```
**Use when**: You want automatic crawling without API (headless mode)

### Option 3: Both Services
```bash
./start_both.sh
```
**Use when**: You need full functionality with automatic crawling

### Option 4: Separate Terminals (Development)
```bash
# Terminal 1: Start API
./start_api.sh

# Terminal 2: Start Background Crawler
./start_crawl.sh
```
**Use when**: You want to see logs from both services separately

## Configuration

### Enable/Disable Background Crawling
Edit `.env`:
```env
# Disable for API-only mode
ENABLE_BACKGROUND_CRAWLING=False

# Enable for automatic crawling
ENABLE_BACKGROUND_CRAWLING=True
```

### Crawl Interval
```env
CRAWL_INTERVAL_HOURS=24  # Crawl every 24 hours
```

### Resource Limits
Each service has its own resource limits set in the start scripts.

## Deployment Scenarios

### Production: Separate Containers
```yaml
# docker-compose.yml
services:
  api:
    build: .
    command: python main.py
    ports:
      - "8000:8000"
  
  crawler:
    build: .
    command: python main_crawl.py
    environment:
      - ENABLE_BACKGROUND_CRAWLING=True
```

### Development: Single Machine
```bash
# Start both in background
./start_both.sh &

# Or use screen/tmux
screen -S api ./start_api.sh
screen -S crawler ./start_crawl.sh
```

### Testing: API Only
```bash
./start_minimal.sh
# Trigger crawls manually via API
curl -X POST http://localhost:8000/api/v1/crawl -d '{"domains": ["example.com"]}'
```

## Monitoring

### API Server
- **Logs**: `data/logs/crawler.log`
- **Health**: `curl http://localhost:8000/api/v1/health`
- **Stats**: `curl http://localhost:8000/api/v1/stats`

### Background Crawler
- **Logs**: Console output + `data/logs/crawler.log`
- **Status**: Check process with `ps aux | grep main_crawl`

## Benefits of Separation

1. **Resource Isolation**: API server doesn't block on crawling
2. **Independent Scaling**: Scale API and crawler separately
3. **Fault Tolerance**: One service failure doesn't affect the other
4. **Flexible Deployment**: Run services on different machines/containers
5. **Development**: Test API without automatic crawling overhead

## Stopping Services

### Stop API
```bash
pkill -f "python main.py"
```

### Stop Crawler
```bash
pkill -f "python main_crawl.py"
```

### Stop All
```bash
./emergency_stop.sh
```

## Notes

- Both services share the same database (`data/crawler_rag.db`)
- Both services can trigger crawls independently
- API-triggered crawls run as background tasks in the API process
- Scheduled crawls run in the crawler service process
- They don't interfere with each other
