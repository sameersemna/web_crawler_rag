# 🚨 CRITICAL: How to Start the Application Safely

## ⚠️ DO NOT USE `python main.py` directly!

If your system is hanging or VS Code is crashing, you **MUST** use the safe start script.

## ✅ CORRECT WAY TO START

### Option 1: Use the Safe Start Script (RECOMMENDED)

```bash
# Make it executable (first time only)
chmod +x start_safe.sh emergency_stop.sh

# Start the application with resource limits
./start_safe.sh
```

This script:
- Sets thread limits BEFORE starting Python
- Applies OS-level resource constraints
- Uses single worker process
- Limits concurrent connections
- Disables background crawling

### Option 2: Manual Start with Environment Variables

```bash
# Set all limits
export OMP_NUM_THREADS=2
export OPENBLAS_NUM_THREADS=2
export MKL_NUM_THREADS=2
export VECLIB_MAXIMUM_THREADS=2
export NUMEXPR_NUM_THREADS=2
export TOKENIZERS_PARALLELISM=false
export MAX_WORKERS=1
export CRAWLER_CONCURRENT_REQUESTS=2
export ENABLE_BACKGROUND_CRAWLING=False

# Apply process limits
ulimit -v 4194304  # 4GB virtual memory
ulimit -u 256      # 256 max processes
ulimit -s 8192     # 8MB stack size

# Start with Uvicorn
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 1 --limit-concurrency 20
```

### Option 3: Docker with Resource Limits (SAFEST)

```bash
# This uses the resource limits defined in docker-compose.yml
docker-compose down
docker-compose up -d

# Monitor
docker stats web_crawler_rag_api
```

## 🛑 Emergency Stop

If the application is hanging or system is unresponsive:

```bash
./emergency_stop.sh
```

Or manually:
```bash
pkill -9 -f "uvicorn.*main:app"
pkill -9 -f "python.*main.py"
```

## 📊 Monitor Resource Usage

### While Application is Running

**Terminal 1** - Application:
```bash
./start_safe.sh
```

**Terminal 2** - Monitor:
```bash
# Real-time system monitor
htop

# Or simple top
top

# Filter for python processes
ps aux | grep python
```

### Check Memory and CPU

```bash
# Memory usage
free -h

# CPU cores being used
nproc

# Application process stats
ps aux | grep -E "uvicorn|python" | grep -v grep
```

## ⚙️ Configuration Levels

### Ultra-Conservative (For Frequent Crashes)

Edit `.env` or set environment variables:
```bash
MAX_WORKERS=1
CRAWLER_CONCURRENT_REQUESTS=1
CRAWLER_MAX_THREADS=1
MAX_EMBEDDING_BATCH_SIZE=8
CHROMADB_MAX_BATCH_SIZE=25
CHUNK_SIZE=250
ENABLE_BACKGROUND_CRAWLING=False
MAX_CRAWL_DEPTH=2
```

### Conservative (Current Default)

Already set in the application:
```bash
MAX_WORKERS=1
CRAWLER_CONCURRENT_REQUESTS=2
CRAWLER_MAX_THREADS=2
MAX_EMBEDDING_BATCH_SIZE=16
CHROMADB_MAX_BATCH_SIZE=50
CHUNK_SIZE=500
ENABLE_BACKGROUND_CRAWLING=False
```

### Moderate (If Ultra-Conservative is Stable)

```bash
MAX_WORKERS=2
CRAWLER_CONCURRENT_REQUESTS=4
CRAWLER_MAX_THREADS=4
MAX_EMBEDDING_BATCH_SIZE=32
CHROMADB_MAX_BATCH_SIZE=100
CHUNK_SIZE=1000
ENABLE_BACKGROUND_CRAWLING=False  # Still keep disabled
```

## 🔍 Troubleshooting

### System Still Hangs

1. **Stop everything immediately**:
   ```bash
   ./emergency_stop.sh
   ```

2. **Check for zombie processes**:
   ```bash
   ps aux | grep -E "python|uvicorn" | grep -v grep
   ```

3. **Use ultra-conservative settings** (see above)

4. **Start with crawling disabled**:
   ```bash
   export ENABLE_BACKGROUND_CRAWLING=False
   ./start_safe.sh
   ```

5. **Test with single domain**:
   ```bash
   # After starting, manually crawl ONE domain
   curl -X POST http://localhost:8000/api/v1/crawl \
     -H "Content-Type: application/json" \
     -d '{"domains": ["example.com"], "max_pages": 5}'
   ```

### VS Code Still Crashes

1. **Close all other VS Code windows**
2. **Disable resource-intensive VS Code extensions**:
   - Pylance (temporarily)
   - Python (if not needed for this project)
   - Any AI assistants
3. **Increase VS Code memory** in settings.json:
   ```json
   {
     "files.maxMemoryForLargeFilesMB": 2048,
     "python.analysis.memory.keepLibraryAst": false
   }
   ```
4. **Run application outside VS Code terminal**:
   - Use a separate terminal application
   - This prevents terminal output from consuming VS Code resources

### Memory Still Growing

1. **Disable OCR** (very memory intensive):
   ```bash
   export ENABLE_OCR=False
   ```

2. **Use smaller embedding model**:
   ```bash
   export EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
   ```

3. **Reduce chunk size further**:
   ```bash
   export CHUNK_SIZE=250
   export CHUNK_OVERLAP=50
   ```

4. **Limit pages per crawl**:
   ```bash
   # In crawler API call, add max_pages parameter
   curl -X POST http://localhost:8000/api/v1/crawl \
     -d '{"domains": ["example.com"], "max_pages": 10}'
   ```

## ✅ Verification Checklist

Before considering the application "stable":

- [ ] Application starts without errors
- [ ] CPU usage stays below 200% (2 cores)
- [ ] Memory usage stays below 2GB
- [ ] VS Code remains responsive
- [ ] Can crawl single domain without hang
- [ ] System doesn't slow down significantly
- [ ] Can run for 10+ minutes without issues

## 📝 Testing Procedure

1. **Clean start**:
   ```bash
   ./emergency_stop.sh
   sleep 5
   ./start_safe.sh
   ```

2. **Wait 2 minutes** for full initialization

3. **Check health**:
   ```bash
   curl http://localhost:8000/api/v1/health
   ```

4. **Monitor resources** (in another terminal):
   ```bash
   watch -n 1 'ps aux | grep python | grep -v grep'
   ```

5. **Test small crawl**:
   ```bash
   curl -X POST http://localhost:8000/api/v1/crawl \
     -H "Content-Type: application/json" \
     -d '{"domains": ["example.com"], "max_pages": 5}'
   ```

6. **Monitor for 5 minutes**:
   - Watch CPU in htop
   - Watch memory usage
   - Verify VS Code stays responsive

7. **If stable**, gradually increase limits

## 🚀 Gradual Scale-Up Procedure

If ultra-conservative settings are stable:

**Week 1**: Test with ultra-conservative
**Week 2**: Increase to conservative (double values)
**Week 3**: Increase batch sizes by 50%
**Week 4**: Add one more worker if stable

Never increase all settings at once!

## 📚 Related Documentation

- [RESOURCE_MANAGEMENT.md](docs/RESOURCE_MANAGEMENT.md) - Complete guide
- [QUICK_FIX.md](docs/QUICK_FIX.md) - Emergency fixes
- [CHECKLIST.md](CHECKLIST.md) - Verification steps

---

## Summary

**DO**: Use `./start_safe.sh`
**DON'T**: Use `python main.py` directly

**DO**: Monitor with `htop` in separate terminal
**DON'T**: Run without monitoring first time

**DO**: Start with background crawling disabled
**DON'T**: Enable automatic crawling until tested

**DO**: Test with single small domain first
**DON'T**: Crawl multiple large sites initially

**DO**: Stop immediately if system slows down
**DON'T**: Wait for complete hang before stopping
