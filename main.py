"""
Main FastAPI Application with Multi-Instance Support
Usage: python main.py [config_file.yaml]
"""
import os
import sys
import argparse
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import time

# AUTO-DETECT and apply optimal resource configuration BEFORE importing other modules
from app.utils.resource_detector import ResourceDetector
optimal_config = ResourceDetector.get_optimal_config()
ResourceDetector.apply_config(optimal_config)

# Set additional environment variables
os.environ.setdefault('TOKENIZERS_PARALLELISM', 'false')

# Set Python recursion limit to prevent stack overflow
sys.setrecursionlimit(1000)

from app.api.routes import router
from app.core.config import settings, reload_settings
from app.core.config_loader import load_instance_config, get_instance_config
from app.core.logging import app_logger, setup_logging
from app.core.database import init_db, initialize_database


# Parse command line arguments
def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Web Crawler RAG API with multi-instance support'
    )
    parser.add_argument(
        'config',
        nargs='?',
        default=None,
        help='YAML configuration file (e.g., islam.yaml, law.yaml)'
    )
    return parser.parse_args()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    instance_name = getattr(settings, 'instance_name', 'default')
    app_logger.info(f"Starting Web Crawler RAG API - Instance: {instance_name}")
    
    # Initialize database
    init_db()
    
    app_logger.info("Application startup complete")
    
    yield
    
    # Shutdown
    app_logger.info("Shutting down Web Crawler RAG API")


# Create FastAPI app
app = FastAPI(
    title="Web Crawler RAG API",
    description="API for crawling websites and performing RAG-based question answering",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure as needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add processing time to response headers"""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


# Exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    app_logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if settings.debug else "An error occurred"
        }
    )


# Include routers
app.include_router(router, prefix="/api/v1", tags=["main"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "Web Crawler RAG API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/api/v1/info")
async def api_info():
    """API information endpoint"""
    instance_name = getattr(settings, 'instance_name', 'default')
    instance_desc = getattr(settings, 'instance_description', 'Default instance')
    
    return {
        "name": "Web Crawler RAG API",
        "version": "1.0.0",
        "instance": instance_name,
        "description": instance_desc,
        "features": [
            "Multi-domain web crawling",
            "PDF processing with OCR",
            "Multilingual support",
            "Vector-based semantic search",
            "RAG with Gemini/DeepSeek LLM",
            "Automatic periodic re-crawling",
            "Detailed source citations",
            "Multi-instance support"
        ],
        "endpoints": {
            "query": "/api/v1/query",
            "query_filtered": "/api/v1/query-filtered",
            "crawl": "/api/v1/crawl",
            "status": "/api/v1/status",
            "health": "/api/v1/health",
            "logs": "/api/v1/logs",
            "stats": "/api/v1/stats"
        }
    }


if __name__ == "__main__":
    import uvicorn
    
    # Parse command line arguments
    args = parse_args()
    
    # Load instance configuration if provided
    if args.config:
        config_path = Path(args.config)
        if not config_path.exists():
            print(f"ERROR: Configuration file not found: {args.config}")
            print("\nAvailable configuration files:")
            for yaml_file in Path('.').glob('*.yaml'):
                print(f"  - {yaml_file.name}")
            sys.exit(1)
        
        # Load YAML configuration
        instance_cfg = load_instance_config(args.config)
        
        # Set environment variables so worker processes inherit them
        os.environ['INSTANCE_NAME'] = instance_cfg.instance_name
        os.environ['INSTANCE_DESCRIPTION'] = instance_cfg.instance_description
        os.environ['API_HOST'] = instance_cfg.host
        os.environ['API_PORT'] = str(instance_cfg.port)
        os.environ['DATABASE_URL'] = f"sqlite:///{instance_cfg.db_path}"
        os.environ['VECTOR_DB_PATH'] = str(instance_cfg.vector_db_path)
        os.environ['DOMAINS_CSV_PATH'] = str(instance_cfg.domains_file)
        
        # Construct log file path from data_dir (for worker processes)
        os.environ['LOG_FILE_PATH'] = str(instance_cfg.logs_dir / "crawler.log")
        
        # Reload settings from updated environment variables
        reload_settings()
        
        # Override settings with instance config (for main process)
        settings.instance_name = instance_cfg.instance_name
        settings.instance_description = instance_cfg.instance_description
        settings.api_host = instance_cfg.host
        settings.api_port = instance_cfg.port
        settings.api_workers = instance_cfg.workers
        settings.database_url = f"sqlite:///{instance_cfg.db_path}"
        settings.vector_db_path = str(instance_cfg.vector_db_path)
        settings.domains_csv_path = str(instance_cfg.domains_file)
        
        # Set log file path from data_dir (not from .env)
        settings.log_file_path = str(instance_cfg.logs_dir / "crawler.log")
        
        # Override crawler settings
        settings.max_crawl_depth = instance_cfg.get('crawler.max_depth', 5)
        settings.crawler_concurrent_requests = instance_cfg.get('crawler.concurrent_requests', 2)
        settings.crawler_download_delay = instance_cfg.get('crawler.download_delay', 1.0)
        settings.crawler_user_agent = instance_cfg.get('crawler.user_agent', 'WebCrawlerBot/1.0')
        socks5_proxy = instance_cfg.get('crawler.socks5_proxy', '')
        settings.crawler_socks5_proxy = socks5_proxy if socks5_proxy else None
        settings.enable_background_crawling = instance_cfg.get('crawler.enable_background', False)
        
        # Override embedding settings
        settings.embedding_model = instance_cfg.get('embeddings.model', 'sentence-transformers/all-MiniLM-L6-v2')
        settings.chunk_size = instance_cfg.get('embeddings.chunk_size', 500)
        settings.chunk_overlap = instance_cfg.get('embeddings.chunk_overlap', 100)
        settings.max_embedding_batch_size = instance_cfg.get('embeddings.batch_size', 32)
        settings.chromadb_max_batch_size = instance_cfg.get('embeddings.chromadb_batch_size', 100)
        
        # Override RAG settings
        settings.rag_top_k_results = instance_cfg.get('rag.top_k_results', 5)
        settings.rag_similarity_threshold = instance_cfg.get('rag.similarity_threshold', 0.5)
        settings.snippet_length = instance_cfg.get('rag.snippet_length', 200)
        settings.default_llm_provider = instance_cfg.get('rag.default_provider', 'gemini')
        settings.llm_temperature = instance_cfg.get('rag.temperature', 0.7)
        
        # Override LLM settings
        settings.gemini_model = instance_cfg.get('llm.gemini_model', 'gemini-2.0-flash-lite')
        
        # Override resource settings
        os.environ['OMP_NUM_THREADS'] = str(instance_cfg.get('resources.num_threads', 4))
        os.environ['OPENBLAS_NUM_THREADS'] = str(instance_cfg.get('resources.num_threads', 4))
        os.environ['MKL_NUM_THREADS'] = str(instance_cfg.get('resources.num_threads', 4))
        settings.enable_ocr = instance_cfg.get('resources.enable_ocr', False)
        
        # Reconfigure logging with instance-specific path
        setup_logging(force_reconfigure=True)
        
        # Reinitialize database with instance-specific path
        initialize_database()
        
        print(f"\n{'='*60}")
        print(f"Starting Instance: {instance_cfg.instance_name}")
        print(f"{'='*60}")
        print(f"Description: {instance_cfg.instance_description}")
        print(f"Port: {instance_cfg.port}")
        print(f"Data directory: {instance_cfg.data_dir}")
        print(f"Database: {instance_cfg.db_path}")
        print(f"Domains file: {instance_cfg.domains_file}")
        print(f"Log file: {instance_cfg.logs_dir / 'crawler.log'}")
        print(f"{'='*60}\n")
    else:
        print("\nNo configuration file specified. Using default settings.")
        print("Usage: python main.py <config_file.yaml>")
        print("\nExample:")
        print("  python main.py islam.yaml")
        print("  python main.py law.yaml\n")
    
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        workers=settings.api_workers,
        reload=settings.debug
    )
