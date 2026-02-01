# Project Structure

Complete overview of the Web Crawler RAG API project structure.

## Directory Tree

```
web_crawler_rag/
├── app/
│   ├── __init__.py
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py              # API endpoint definitions
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py              # Configuration management
│   │   ├── database.py            # Database connection & session
│   │   └── logging.py             # Logging configuration
│   ├── models/
│   │   ├── __init__.py
│   │   ├── database.py            # SQLAlchemy models
│   │   └── schemas.py             # Pydantic models for API
│   ├── services/
│   │   ├── __init__.py
│   │   ├── crawler.py             # Web crawler service
│   │   ├── pdf_processor.py      # PDF extraction & OCR
│   │   ├── vector_db.py           # Vector database operations
│   │   ├── llm_service.py         # LLM API integration
│   │   ├── rag_service.py         # RAG query processing
│   │   └── scheduler.py           # Background task scheduler
│   └── utils/
│       ├── __init__.py
│       └── text_utils.py          # Text processing utilities
├── data/
│   ├── logs/
│   │   └── crawler.log            # Application logs
│   ├── vector_db/                 # ChromaDB storage
│   ├── domains.csv                # List of domains to crawl
│   └── crawler_rag.db            # SQLite database
├── config/                        # Additional configuration files
├── docs/
│   ├── API_USAGE.md              # API usage examples
│   └── SUGGESTIONS.md            # Recommended improvements
├── tests/
│   ├── __init__.py
│   └── test_api.py               # API tests
├── main.py                        # FastAPI application entry point
├── requirements.txt               # Python dependencies
├── .env.example                   # Environment variables template
├── .env                          # Environment variables (not in git)
├── .gitignore                    # Git ignore rules
├── Dockerfile                    # Docker container definition
├── docker-compose.yml            # Docker Compose configuration
├── setup.sh                      # Setup script
└── README.md                     # Project documentation
```

## Core Components

### 1. Application Entry Point

**File:** `main.py`
- FastAPI application initialization
- Middleware setup
- Router registration
- Lifecycle management

### 2. API Layer

**Directory:** `app/api/`

- **routes.py**: All API endpoints
  - `/api/v1/query` - RAG queries
  - `/api/v1/crawl` - Trigger crawls
  - `/api/v1/status` - Check status
  - `/api/v1/health` - Health check
  - `/api/v1/logs` - View logs
  - `/api/v1/stats` - Statistics

### 3. Core Layer

**Directory:** `app/core/`

- **config.py**: Settings management using Pydantic
- **database.py**: Database connection and session handling
- **logging.py**: Centralized logging with Loguru

### 4. Models Layer

**Directory:** `app/models/`

- **database.py**: SQLAlchemy ORM models
  - `CrawledPage` - Stores crawled content
  - `CrawlLog` - Crawl activity logs
  - `Domain` - Domain management
  - `VectorEmbedding` - Vector ID mapping

- **schemas.py**: Pydantic models for API
  - Request/response validation
  - Type safety
  - Automatic documentation

### 5. Services Layer

**Directory:** `app/services/`

Core business logic:

- **crawler.py**: Web crawling
  - Async HTTP requests
  - HTML parsing
  - Link extraction
  - Sitemap support

- **pdf_processor.py**: PDF handling
  - Text extraction
  - OCR processing
  - Multi-language support

- **vector_db.py**: Vector operations
  - Embedding generation
  - Semantic search
  - ChromaDB management

- **llm_service.py**: LLM integration
  - Gemini API
  - DeepSeek API
  - Prompt engineering

- **rag_service.py**: RAG orchestration
  - Query processing
  - Context retrieval
  - Answer generation
  - Source citation

- **scheduler.py**: Background tasks
  - Periodic crawling
  - Domain monitoring
  - CSV updates

### 6. Utilities

**Directory:** `app/utils/`

- **text_utils.py**: Common utilities
  - URL validation
  - Text cleaning
  - Language detection
  - File size formatting

## Data Flow

### Crawling Flow

```
CSV File → Scheduler → Crawler → PDF Processor → Database → Vector DB
    ↓          ↓           ↓            ↓            ↓           ↓
domains.csv  Load    HTTP Requests   Extract    Store     Embed
           Domains    Parse HTML      OCR      Content   Chunks
```

### Query Flow

```
User Query → API → RAG Service → Vector DB → LLM Service → Response
     ↓        ↓         ↓            ↓           ↓            ↓
  Request  Validate  Retrieve   Search for  Generate    Format
           Input    Context    Similar     Answer      Sources
```

## Configuration

### Environment Variables

**File:** `.env`

Key settings:
- API configuration (host, port, workers)
- LLM API keys (Gemini, DeepSeek)
- Vector DB settings
- Crawler parameters
- Logging configuration
- Database URL

### domains.csv Format

```csv
domain
example.com
docs.python.org
fastapi.tiangolo.com
```

## Database Schema

### Tables

1. **domains**
   - Domain tracking
   - Crawl scheduling
   - Status management

2. **crawled_pages**
   - Page content
   - Metadata
   - Checksums for change detection

3. **crawl_logs**
   - Activity logging
   - Performance metrics
   - Error tracking

4. **vector_embeddings**
   - Vector ID mapping
   - Chunk references

## API Design

### RESTful Endpoints

- `POST /api/v1/query` - Submit queries
- `POST /api/v1/crawl` - Trigger crawls
- `GET /api/v1/status` - Check status
- `GET /api/v1/health` - Health check
- `GET /api/v1/logs` - View logs
- `GET /api/v1/stats` - Get statistics
- `DELETE /api/v1/domain/{domain}` - Delete domain

### Response Format

All responses follow consistent structure:
```json
{
  "query": "...",
  "answer": "...",
  "sources": [...],
  "metadata": {...}
}
```

## Dependencies

### Core Libraries

- **FastAPI**: Web framework
- **Uvicorn**: ASGI server
- **Pydantic**: Data validation
- **SQLAlchemy**: ORM
- **ChromaDB**: Vector database
- **Sentence Transformers**: Embeddings

### Crawling

- **aiohttp**: Async HTTP
- **BeautifulSoup4**: HTML parsing
- **Scrapy**: Advanced crawling
- **Playwright**: JavaScript rendering

### PDF Processing

- **PyPDF2**: PDF reading
- **pdfplumber**: Complex layouts
- **pytesseract**: OCR
- **pdf2image**: PDF to images

### LLM Integration

- **google-generativeai**: Gemini
- **openai**: DeepSeek (OpenAI-compatible)

### Scheduling

- **APScheduler**: Background tasks

### Logging

- **Loguru**: Advanced logging

## Testing

### Test Structure

```
tests/
├── __init__.py
├── test_api.py          # API endpoint tests
├── test_crawler.py      # Crawler tests
├── test_pdf.py          # PDF processing tests
├── test_vector_db.py    # Vector DB tests
└── test_rag.py          # RAG service tests
```

### Running Tests

```bash
# All tests
pytest tests/

# With coverage
pytest tests/ --cov=app --cov-report=html

# Specific test file
pytest tests/test_api.py -v
```

## Deployment

### Docker

```bash
# Build
docker build -t web-crawler-rag .

# Run
docker run -p 8000:8000 web-crawler-rag
```

### Docker Compose

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

### Production Checklist

- [ ] Set `DEBUG=False`
- [ ] Configure PostgreSQL
- [ ] Add Redis for caching
- [ ] Set up monitoring
- [ ] Configure CORS properly
- [ ] Add authentication
- [ ] Set up SSL/TLS
- [ ] Configure rate limiting
- [ ] Set up backup strategy
- [ ] Configure log rotation
- [ ] Add health checks
- [ ] Set up CI/CD

## Monitoring

### Logs

Location: `data/logs/crawler.log`

Log levels:
- DEBUG: Detailed information
- INFO: General information
- WARNING: Warning messages
- ERROR: Error messages
- CRITICAL: Critical issues

### Metrics to Monitor

- Request rate
- Response time
- Error rate
- Crawl success rate
- Vector DB size
- Database size
- Memory usage
- CPU usage

## Scalability Considerations

### Horizontal Scaling

- Run multiple API instances behind load balancer
- Use shared PostgreSQL database
- Use shared Redis for caching
- Centralized vector database

### Vertical Scaling

- Increase worker processes
- Allocate more memory
- Use faster storage (SSD)

### Performance Tuning

- Adjust chunk size
- Optimize embedding model
- Use connection pooling
- Implement caching
- Batch operations

## Security

### Best Practices

1. **API Keys**: Store in environment variables
2. **Database**: Use strong passwords
3. **CORS**: Restrict origins
4. **Rate Limiting**: Prevent abuse
5. **Input Validation**: Sanitize all inputs
6. **Logging**: Don't log sensitive data

## Maintenance

### Regular Tasks

- Monitor disk usage
- Check log files
- Review error rates
- Update dependencies
- Backup database
- Clean old data
- Optimize database

### Updates

```bash
# Update dependencies
pip install --upgrade -r requirements.txt

# Database migrations
alembic upgrade head
```

## Support & Resources

- **Documentation**: `/docs` endpoint
- **API Docs**: Swagger UI at `/docs`
- **GitHub**: [Repository link]
- **Issues**: [Issue tracker]

## Version History

- v1.0.0 (Initial Release)
  - Web crawling with sitemap support
  - PDF processing with OCR
  - RAG with Gemini/DeepSeek
  - Background scheduling
  - Comprehensive logging
