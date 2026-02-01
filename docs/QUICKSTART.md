# Quick Start Guide

Get up and running with the Web Crawler RAG API in minutes.

## Prerequisites

- Python 3.9 or higher
- Tesseract OCR (for PDF processing)
- 4GB RAM minimum
- 10GB free disk space

## Installation

### 1. Clone or Extract the Project

```bash
cd web_crawler_rag
```

### 2. Run Setup Script

```bash
chmod +x setup.sh
./setup.sh
```

This will:
- Create virtual environment
- Install dependencies
- Create necessary directories
- Generate example files

### 3. Configure Environment

Edit `.env` file and add your API keys:

```bash
nano .env
```

**Required settings:**
```env
GEMINI_API_KEY=your_gemini_api_key_here
DEEPSEEK_API_KEY=your_deepseek_api_key_here
```

### 4. Add Domains to Crawl

Edit `data/domains.csv`:

```csv
domain
docs.python.org
fastapi.tiangolo.com
example.com
```

### 5. Start the Server

```bash
# Activate virtual environment
source venv/bin/activate

# Run the server
python main.py
```

The API will start on `http://localhost:8000`

## First Steps

### 1. Check Health

```bash
curl http://localhost:8000/api/v1/health
```

### 2. Start Crawling

```bash
curl -X POST http://localhost:8000/api/v1/crawl \
  -H "Content-Type: application/json" \
  -d '{
    "domains": ["docs.python.org"],
    "force_recrawl": false
  }'
```

### 3. Check Status

```bash
curl http://localhost:8000/api/v1/status
```

### 4. Ask a Question

```bash
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is Python?"
  }'
```

## Web Interface

Access the interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Common Issues

### Issue: "Tesseract not found"

**Solution:**
```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr

# macOS
brew install tesseract

# Verify installation
tesseract --version
```

### Issue: "Port 8000 already in use"

**Solution:**
Change the port in `.env`:
```env
API_PORT=8080
```

### Issue: "API key invalid"

**Solution:**
1. Check your API keys in `.env`
2. Ensure no extra spaces
3. Verify keys are valid

### Issue: "No data found"

**Solution:**
1. Wait for initial crawl to complete
2. Check crawl status
3. View logs for errors

## Production Deployment

### Using Docker

```bash
# Build
docker build -t web-crawler-rag .

# Run
docker run -p 8000:8000 --env-file .env web-crawler-rag
```

### Using Docker Compose

```bash
docker-compose up -d
```

## Environment Variables Reference

### Essential

```env
GEMINI_API_KEY=...           # Required for Gemini
DEEPSEEK_API_KEY=...         # Required for DeepSeek
DEFAULT_LLM_PROVIDER=gemini  # gemini or deepseek
```

### Optional

```env
# API
API_PORT=8000
DEBUG=False

# Crawler
CRAWL_INTERVAL_HOURS=24
MAX_CRAWL_DEPTH=5

# OCR
ENABLE_OCR=True
OCR_LANGUAGES=eng+ara+hin+urd

# Vector DB
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
```

## Monitoring

### View Logs

```bash
tail -f data/logs/crawler.log
```

### Check Statistics

```bash
curl http://localhost:8000/api/v1/stats
```

### View Crawl Logs

```bash
curl http://localhost:8000/api/v1/logs?limit=50
```

## Customization

### Change Crawl Frequency

Edit `.env`:
```env
CRAWL_INTERVAL_HOURS=12  # Crawl every 12 hours
```

### Adjust Search Results

```env
RAG_TOP_K_RESULTS=10      # Return top 10 results
SNIPPET_LENGTH=500        # 500 character snippets
```

### Enable/Disable Features

```env
ENABLE_BACKGROUND_CRAWLING=True
ENABLE_SITEMAP_CRAWLING=True
RESPECT_ROBOTS_TXT=True
```

## Testing

Run tests:

```bash
pytest tests/
```

Run with coverage:

```bash
pytest tests/ --cov=app
```

## Stopping the Server

Press `Ctrl+C` in the terminal or:

```bash
pkill -f "python main.py"
```

## Next Steps

1. Read the full [README.md](../README.md)
2. Explore [API Usage Examples](API_USAGE.md)
3. Review [Suggestions](SUGGESTIONS.md) for improvements
4. Check [Project Structure](PROJECT_STRUCTURE.md)

## Support

- **Documentation**: http://localhost:8000/docs
- **Logs**: `data/logs/crawler.log`
- **Issues**: Check error messages in logs

## Tips

1. **Start Small**: Begin with 1-2 domains
2. **Monitor Resources**: Watch CPU/memory usage
3. **Check Logs**: Regularly review for errors
4. **Backup Data**: Save `data/` directory
5. **Update Regularly**: Keep dependencies current

## Example Workflow

```bash
# 1. Start server
python main.py

# 2. In another terminal, trigger crawl
curl -X POST http://localhost:8000/api/v1/crawl \
  -H "Content-Type: application/json" \
  -d '{"domains": ["docs.python.org"]}'

# 3. Wait a few minutes, then query
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"query": "How do I use async/await in Python?"}'

# 4. Check stats
curl http://localhost:8000/api/v1/stats
```

## Troubleshooting Commands

```bash
# Check if server is running
curl http://localhost:8000/

# Check health
curl http://localhost:8000/api/v1/health

# View recent logs
tail -n 100 data/logs/crawler.log

# Check database
sqlite3 data/crawler_rag.db "SELECT COUNT(*) FROM crawled_pages;"

# List all domains
curl http://localhost:8000/api/v1/status | python -m json.tool
```

## Performance Tips

1. Increase concurrent requests:
   ```env
   CRAWLER_CONCURRENT_REQUESTS=32
   ```

2. Use faster embedding model:
   ```env
   EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
   ```

3. Reduce chunk size for faster processing:
   ```env
   CHUNK_SIZE=500
   ```

## Security Notes

- **Never commit `.env`** to version control
- Use **strong API keys**
- Enable **rate limiting** in production
- Configure **CORS** appropriately
- Use **HTTPS** in production

Ready to build something amazing! 🚀
