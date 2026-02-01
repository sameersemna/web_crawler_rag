# Quick Resource Configuration

⚠️ **System experiencing hangs or crashes?** Use these configurations:

## Emergency "Conservative" Mode

Copy this to your `.env` file or docker-compose.yml:

```bash
# Minimal resource usage
MAX_WORKERS=1
CRAWLER_CONCURRENT_REQUESTS=2
CRAWLER_MAX_THREADS=2
MAX_EMBEDDING_BATCH_SIZE=16
CHROMADB_MAX_BATCH_SIZE=50
OMP_NUM_THREADS=2
OPENBLAS_NUM_THREADS=2
MKL_NUM_THREADS=2
VECLIB_MAXIMUM_THREADS=2
NUMEXPR_NUM_THREADS=2
ENABLE_BACKGROUND_CRAWLING=False
```

Update Docker limits in `docker-compose.yml`:
```yaml
deploy:
  resources:
    limits:
      cpus: '2.0'
      memory: 2G
```

## Quick Test

After applying changes:

```bash
# Rebuild and restart
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# Monitor resources
docker stats web_crawler_rag_api

# Check logs for errors
docker-compose logs -f | grep -i "error\|warning"
```

## Still Having Issues?

1. **Check system resources**: `htop` or `top`
2. **Verify Docker limits**: `docker inspect web_crawler_rag_api | grep -i memory`
3. **Check VS Code**: Close unnecessary extensions and tabs
4. **Review logs**: `tail -100 data/logs/crawler.log`

See [RESOURCE_MANAGEMENT.md](RESOURCE_MANAGEMENT.md) for complete documentation.
