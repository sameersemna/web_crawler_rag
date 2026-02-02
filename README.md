# Web Crawler RAG API

A comprehensive FastAPI-based web crawler and Retrieval-Augmented Generation (RAG) system that crawls websites, extracts content (including PDFs with OCR), and provides intelligent question-answering capabilities using LLMs.

> **⚠️ Important**: This application includes resource limits to prevent system hangs. See [Resource Management Guide](docs/RESOURCE_MANAGEMENT.md) for configuration options.

## Features

### Core Functionality
- 🕷️ **Advanced Web Crawling**
  - Multi-domain support via CSV input
  - Sitemap.xml detection and parsing
  - Robots.txt compliance
  - Depth-limited recursive crawling
  - Concurrent request handling

- 📄 **PDF Processing**
  - Text extraction from PDFs
  - OCR for scanned documents
  - Multi-language OCR support (English, Arabic, Hindi, Urdu)
  - Page-level text extraction for citations

- 🌐 **Multilingual Support**
  - Content processing in multiple languages
  - OCR support for Arabic, Urdu, Hindi, English

- 🔍 **Vector Search**
  - Semantic search using sentence transformers
  - ChromaDB for efficient vector storage
  - Configurable similarity thresholds

- 🤖 **RAG with Multiple LLMs**
  - Gemini API integration
  - DeepSeek API integration
  - Configurable temperature and parameters
  - Context-aware answer generation

- 📊 **Source Citations**
  - Exact URL references
  - PDF page numbers
  - Highlighted text snippets
  - Similarity scores

- ⏰ **Automatic Crawling**
  - Periodic re-crawling (default: 24 hours)
  - Background scheduler
  - Configurable intervals per domain

- 📝 **Comprehensive Logging**
  - Timestamped crawl logs
  - Success/failure tracking
  - Performance metrics

## Installation

### Prerequisites
- Python 3.9+
- Tesseract OCR (for PDF OCR functionality)

### Install Tesseract OCR

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr
sudo apt-get install tesseract-ocr-ara tesseract-ocr-hin tesseract-ocr-urd
```

**macOS:**
```bash
brew install tesseract
brew install tesseract-lang
```

**Windows:**
Download from: https://github.com/UB-Mannheim/tesseract/wiki

### Python Dependencies

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Configuration

### Environment Setup

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Edit `.env` and configure your settings:

```env
# Required: Add your LLM API keys
GEMINI_API_KEY=your_gemini_api_key
DEEPSEEK_API_KEY=your_deepseek_api_key

# Optional: Customize other settings
DEFAULT_LLM_PROVIDER=gemini  # or deepseek
CRAWL_INTERVAL_HOURS=24
ENABLE_OCR=True
```

### Domain Configuration

Create a CSV file with domains to crawl at `./data/domains.csv`:

```csv
domain
example.com
wikipedia.org
docs.python.org
```

The system will automatically detect and create this file with examples if it doesn't exist.

## Usage

### Starting the Server

```bash
# Development mode with auto-reload
python main.py

# Production mode with Uvicorn
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

The API will be available at `http://localhost:8000`

### API Documentation

Interactive API documentation is available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## API Endpoints

### 1. Query RAG System

**POST** `/api/v1/query`

Ask questions based on crawled website content.

**Request:**
```json
{
  "query": "What are the main features of Python?",
  "llm_provider": "gemini",
  "context": "Focus on Python 3.x features",
  "top_k": 5,
  "snippet_length": 300,
  "temperature": 0.7,
  "include_sources": true
}
```

**Response:**
```json
{
  "query": "What are the main features of Python?",
  "answer": "Based on the crawled documentation, Python's main features include...",
  "sources": [
    {
      "url": "https://docs.python.org/3/tutorial/introduction.html",
      "domain": "docs.python.org",
      "title": "An Informal Introduction to Python",
      "snippet": "Python is an easy to learn, powerful programming language...",
      "similarity_score": 0.89,
      "page_number": null,
      "highlighted_text": "Python is an easy to learn, powerful programming language",
      "content_type": "html"
    }
  ],
  "llm_provider": "gemini",
  "confidence_score": 0.85,
  "processing_time_ms": 1250.5,
  "timestamp": "2026-01-31T12:00:00Z"
}
```

### 2. Trigger Manual Crawl

**POST** `/api/v1/crawl`

Manually trigger crawling of specific domains.

**Request:**
```json
{
  "domains": ["example.com", "test.org"],
  "force_recrawl": false
}
```

### 3. Get Crawl Status

**GET** `/api/v1/status`

Check the status of all domains.

**Response:**
```json
{
  "domains": [
    {
      "domain": "example.com",
      "status": "completed",
      "pages_crawled": 42,
      "last_crawl_time": "2026-01-31T10:00:00Z",
      "next_crawl_time": "2026-02-01T10:00:00Z",
      "error_message": null
    }
  ],
  "total_pages_in_db": 150,
  "last_update": "2026-01-31T12:00:00Z"
}
```

### 4. Health Check

**GET** `/api/v1/health`

Check system health and service availability.

### 5. View Logs

**GET** `/api/v1/logs?limit=100&domain=example.com`

Retrieve crawl activity logs.

### 6. Get Statistics

**GET** `/api/v1/stats`

Get system-wide statistics.

### 7. Delete Domain

**DELETE** `/api/v1/domain/{domain_name}`

Remove a domain and all its crawled data.

## Architecture

### Components

1. **Web Crawler** (`app/services/crawler.py`)
   - Async web crawling with aiohttp
   - HTML parsing with BeautifulSoup
   - Sitemap.xml support
   - Robots.txt compliance

2. **PDF Processor** (`app/services/pdf_processor.py`)
   - PyPDF2 for text extraction
   - pdfplumber for complex layouts
   - Tesseract OCR for scanned documents

3. **Vector Database** (`app/services/vector_db.py`)
   - ChromaDB for vector storage
   - Sentence transformers for embeddings
   - Semantic search capabilities

4. **LLM Service** (`app/services/llm_service.py`)
   - Gemini API integration
   - DeepSeek API integration
   - Prompt engineering for RAG

5. **RAG Service** (`app/services/rag_service.py`)
   - Combines vector search + LLM
   - Source citation generation
   - Confidence scoring

6. **Scheduler** (`app/services/scheduler.py`)
   - Background crawling
   - Periodic domain updates
   - CSV monitoring

### Database Schema

**Domains Table:**
- Domain tracking and scheduling
- Crawl status and statistics
- Error tracking

**Crawled Pages Table:**
- Page content storage
- Metadata and checksums
- Change detection

**Crawl Logs Table:**
- Activity logging
- Performance metrics
- Error tracking

**Vector Embeddings Table:**
- Vector ID mapping
- Chunk association

## Advanced Configuration

### Custom Chunk Size

Adjust text chunking for embeddings:

```env
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
```

### Crawler Settings

```env
CRAWLER_CONCURRENT_REQUESTS=16
CRAWLER_DOWNLOAD_DELAY=1
MAX_CRAWL_DEPTH=5
```

### OCR Languages

Configure OCR language support:

```env
OCR_LANGUAGES=eng+ara+hin+urd+fra+deu
```

### Vector Database

Switch between ChromaDB and FAISS:

```env
VECTOR_DB_TYPE=chromadb  # or faiss
```

## Monitoring & Maintenance

### View Logs

Logs are stored in `./data/logs/crawler.log` with automatic rotation.

```bash
tail -f ./data/logs/crawler.log
```

### Database Maintenance

The SQLite database is located at `./data/crawler_rag.db`

```bash
sqlite3 ./data/crawler_rag.db
```

### Vector Database

ChromaDB data is stored in `./data/vector_db/`

## Troubleshooting

### OCR Not Working

Ensure Tesseract is installed and in PATH:
```bash
tesseract --version
```

### Memory Issues

For large crawls, increase chunk size or limit crawl depth:
```env
MAX_CRAWL_DEPTH=3
CHUNK_SIZE=500
```

### API Key Errors

Verify your API keys are correctly set in `.env`:
```bash
echo $GEMINI_API_KEY
echo $DEEPSEEK_API_KEY
```

## Performance Optimization

1. **Concurrent Requests**: Adjust `CRAWLER_CONCURRENT_REQUESTS`
2. **Embedding Model**: Use smaller models for faster processing
3. **Database**: Switch to PostgreSQL for production
4. **Caching**: Implement Redis for query caching
5. **Rate Limiting**: Adjust per endpoint as needed

## Security Considerations

1. **API Keys**: Never commit `.env` to version control
2. **Rate Limiting**: Configure appropriate limits
3. **Input Validation**: All inputs are validated via Pydantic
4. **CORS**: Configure allowed origins in production
5. **Database**: Use proper authentication for production databases

## Development

### Running Tests

```bash
pytest tests/ -v --cov=app
```

### Code Style

```bash
black app/
flake8 app/
mypy app/
```

## Production Deployment

### Docker Deployment

```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-ara \
    tesseract-ocr-hin \
    tesseract-ocr-urd \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Environment Variables for Production

```env
DEBUG=False
API_WORKERS=4
DATABASE_URL=postgresql://user:pass@localhost/db
```

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - See LICENSE file for details

## Additional Documentation

- [API Usage Guide](docs/API_USAGE.md) - Detailed API endpoint documentation
- [Project Structure](docs/PROJECT_STRUCTURE.md) - Code organization overview
- [Quick Start Guide](docs/QUICKSTART.md) - Get up and running quickly
- [Resource Management](docs/RESOURCE_MANAGEMENT.md) - **⚠️ Important: Prevent system hangs and crashes**
- [Suggestions](docs/SUGGESTIONS.md) - Enhancement ideas

## Support

For issues and questions:
- GitHub Issues: [Report bugs]
- Documentation: [API docs]
- Email: support@example.com

## Roadmap

- [ ] Support for more document types (DOCX, Excel)
- [ ] Real-time crawling with webhooks
- [ ] Advanced caching mechanisms
- [ ] Multi-tenant support
- [ ] GraphQL API
- [ ] Elasticsearch integration
- [ ] Advanced analytics dashboard
- [ ] Kubernetes deployment configs


sqlite3 data/crawler_rag.db "SELECT COUNT(*) FROM vector_embeddings;"
kill -9 $(lsof -t -i:8000)