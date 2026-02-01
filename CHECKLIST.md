# ✅ POST-IMPLEMENTATION CHECKLIST

Use this checklist after applying the resource limits.

## 1. Rebuild the Container

```bash
cd /home/sameer/Shared/Sync/Private/Work/Projects/emaanlib/web_crawler_rag

# Option A: Use the convenience script
./restart_with_limits.sh

# Option B: Manual steps
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

**Status**: ⬜ Container rebuilt successfully

## 2. Verify Resource Limits Applied

```bash
# Check CPU limit (should show 4000000000 for 4 cores)
docker inspect web_crawler_rag_api | grep NanoCpus

# Check memory limit (should show 4294967296 for 4GB)
docker inspect web_crawler_rag_api | grep Memory
```

**Status**: ⬜ Limits verified

## 3. Test Container Health

```bash
# Check if container is running
docker ps | grep web_crawler_rag_api

# Test health endpoint
curl http://localhost:8000/api/v1/health

# Expected response:
# {"status":"healthy","timestamp":"..."}
```

**Status**: ⬜ Container healthy

## 4. Monitor Initial Resource Usage

```bash
# Open in a separate terminal
docker stats web_crawler_rag_api
```

Watch for:
- CPU% should be under 400% (4 cores × 100%)
- Memory should be under 4GB
- No rapid growth in memory

**Status**: ⬜ Resources stable

## 5. Check Application Logs

```bash
# View recent logs
docker-compose logs --tail=100

# Follow logs in real-time
docker-compose logs -f
```

Look for:
- ✅ "Application startup complete"
- ✅ "Vector database initialized successfully"
- ❌ No "OutOfMemory" errors
- ❌ No "Connection pool exhausted" errors

**Status**: ⬜ No errors in logs

## 6. Test with a Small Crawl

```bash
# Trigger a crawl for a single domain
curl -X POST http://localhost:8000/api/v1/crawl/example.com
```

Monitor:
- `docker stats` - CPU and memory usage
- `htop` or `top` - system resources
- VS Code remains responsive

**Status**: ⬜ Crawl completed without hang

## 7. System Stability Check

While crawl is running, verify:

**Terminal 1**: `docker stats web_crawler_rag_api`
- CPU stays below 400%
- Memory stays below 4GB

**Terminal 2**: `docker-compose logs -f`
- No error messages
- Normal operation logs

**Terminal 3**: `htop`
- System responsive
- VS Code doesn't freeze

**Status**: ⬜ System remains stable

## 8. Optional: Stress Test

If the above passed, try crawling multiple domains:

```bash
# Add domains to data/domains.csv
echo "example.com" >> data/domains.csv
echo "httpbin.org" >> data/domains.csv

# Trigger crawl for all domains
curl -X POST http://localhost:8000/api/v1/crawl
```

**Status**: ⬜ Multiple crawls stable

## 9. Verify Configuration

Check that environment variables are set:

```bash
docker exec web_crawler_rag_api env | grep -E "MAX_WORKERS|CRAWLER_|OMP_|MKL_"
```

Should show:
```
MAX_WORKERS=2
CRAWLER_CONCURRENT_REQUESTS=4
CRAWLER_MAX_THREADS=4
OMP_NUM_THREADS=4
...
```

**Status**: ⬜ Environment variables correct

## 10. Final Check

- ⬜ Container runs without crashing
- ⬜ System doesn't hang during crawl
- ⬜ VS Code remains usable
- ⬜ CPU usage controlled
- ⬜ Memory usage controlled
- ⬜ No errors in logs

## Troubleshooting

### If System Still Hangs

1. **Reduce limits further** - See [QUICK_FIX.md](QUICK_FIX.md)
2. **Check current usage**: `docker stats`
3. **Review logs**: `docker-compose logs | tail -200`
4. **Try conservative config**:
   ```bash
   # Edit docker-compose.yml
   MAX_WORKERS=1
   CRAWLER_CONCURRENT_REQUESTS=2
   cpus: '2.0'
   memory: 2G
   ```

### If Container Won't Start

```bash
# Check logs for errors
docker-compose logs

# Rebuild from scratch
docker-compose down -v
docker-compose build --no-cache
docker-compose up
```

### If Need More Performance

See "Aggressive" configuration in [RESOURCE_MANAGEMENT.md](RESOURCE_MANAGEMENT.md).

## Results

After completing this checklist:

✅ **Success Criteria**:
- Container runs stably
- System doesn't hang
- VS Code remains responsive
- Resource usage controlled

❌ **If Still Having Issues**:
- Review [QUICK_FIX.md](QUICK_FIX.md) for emergency config
- Check [RESOURCE_MANAGEMENT.md](RESOURCE_MANAGEMENT.md) for tuning
- Consider disabling background crawling: `ENABLE_BACKGROUND_CRAWLING=False`

## Documentation References

- [Changes Applied](CHANGES_APPLIED.md) - What was changed
- [Quick Fix](QUICK_FIX.md) - Emergency configurations
- [Resource Management](RESOURCE_MANAGEMENT.md) - Complete guide
- [Implementation Summary](../RESOURCE_LIMITS_SUMMARY.md) - Technical details

---

**Date Completed**: _______________

**Notes**: 


**System Specs**:
- CPU Cores: _______
- RAM: _______GB
- OS: Linux

**Configuration Used**:
- [ ] Conservative (2 cores, 2GB)
- [ ] Balanced (4 cores, 4GB) ← Default
- [ ] Aggressive (8 cores, 8GB)
- [ ] Custom: _________________
