# Multi-Instance Web Crawler RAG

This project now supports running multiple independent instances with separate configurations, databases, and domains.

## Quick Start

### 1. Migration (First Time Only)

If you have existing data, migrate it to the Islam instance:

```bash
./migrate_to_multi_instance.sh
```

This will:
- Install PyYAML
- Move existing `data/*` to `data/islam/`
- Create `data/law/` template
- Preserve all your crawled data and embeddings

### 2. Running Instances

**Start Islam instance (port 8000):**
```bash
python main.py islam.yaml
```

**Start Law instance (port 8001):**
```bash
python main.py law.yaml
```

**Run both simultaneously:**
```bash
# Terminal 1
python main.py islam.yaml

# Terminal 2
python main.py law.yaml
```

### 3. Creating New Instances

1. **Copy the template:**
   ```bash
   cp .yaml.example medical.yaml
   ```

2. **Edit the configuration:**
   ```yaml
   instance:
     name: "medical"
     description: "Medical knowledge base"
   
   server:
     port: 8002  # Different port!
   
   paths:
     data_dir: "data/medical"
     domains_file: "data/medical/domains.csv"
   ```

3. **Create data directory and domains:**
   ```bash
   mkdir -p data/medical
   echo "domain" > data/medical/domains.csv
   echo "mayoclinic.org" >> data/medical/domains.csv
   echo "webmd.com" >> data/medical/domains.csv
   ```

4. **Start the instance:**
   ```bash
   python main.py medical.yaml
   ```

## Configuration Files

### Instance YAML Structure

Each instance has its own YAML configuration file:

```yaml
instance:
  name: "instance-id"           # Unique identifier
  description: "Description"    # Human-readable description

server:
  port: 8000                     # API port (must be unique per instance)
  host: "0.0.0.0"
  workers: 2
  timeout: 30

paths:
  data_dir: "data/instance-id"  # Instance data directory
  domains_file: "data/instance-id/domains.csv"

database:
  db_name: "crawler_rag.db"
  vector_db_dir: "vector_db"
  logs_dir: "logs"

crawler:
  max_depth: 5
  concurrent_requests: 2
  download_delay: 1.0
  # ... more crawler settings

embeddings:
  model: "sentence-transformers/all-MiniLM-L6-v2"
  chunk_size: 500
  chunk_overlap: 100
  # ... more embedding settings

rag:
  top_k_results: 5
  similarity_threshold: 0.5
  # ... more RAG settings

llm:
  gemini_model: "gemini-2.0-flash-lite"
  deepseek_model: "deepseek-chat"

resources:
  num_threads: 4
  max_crawler_threads: 4
  enable_ocr: false
```

### Environment Variables (.env)

API keys and sensitive data stay in `.env`:

```env
# API Keys (shared across all instances)
GEMINI_API_KEY=your_key_here
DEEPSEEK_API_KEY=your_key_here

# Global defaults (can be overridden by YAML)
DEFAULT_LLM_PROVIDER=gemini
```

## Directory Structure

```
web_crawler_rag/
├── islam.yaml              # Islam instance config
├── law.yaml                # Law instance config
├── .yaml.example           # Template for new instances
├── data/
│   ├── islam/              # Islam instance data
│   │   ├── domains.csv
│   │   ├── crawler_rag.db
│   │   ├── vector_db/
│   │   └── logs/
│   └── law/                # Law instance data
│       ├── domains.csv
│       ├── crawler_rag.db
│       ├── vector_db/
│       └── logs/
├── main.py                 # Main application
└── ...
```

## API Endpoints

Each instance runs independently on its own port:

**Islam instance (port 8000):**
- Query: `http://localhost:8000/api/v1/query`
- Info: `http://localhost:8000/api/v1/info`

**Law instance (port 8001):**
- Query: `http://localhost:8001/api/v1/query`
- Info: `http://localhost:8001/api/v1/info`

## Example Usage

```bash
# Query Islam instance
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is tawheed?"}'

# Query Law instance
curl -X POST http://localhost:8001/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is contract law?"}'
```

## Benefits of Multi-Instance

1. **Isolation**: Each domain has its own database and embeddings
2. **Specialization**: Different RAG settings per topic
3. **Scalability**: Run instances on different ports/servers
4. **Organization**: Clear separation of content types
5. **Resource Control**: Independent resource limits per instance

## Tips

- Use different ports for each instance (8000, 8001, 8002, etc.)
- Keep API keys in `.env` (shared across instances)
- Instance-specific settings go in YAML files
- Each instance can use different embedding models or LLM settings
- Monitor each instance separately via its `/api/v1/info` endpoint
