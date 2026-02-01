"""
Main FastAPI Application
"""
import os
import sys
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import time

# Set resource limits BEFORE importing other modules
os.environ.setdefault('OMP_NUM_THREADS', '2')
os.environ.setdefault('OPENBLAS_NUM_THREADS', '2')
os.environ.setdefault('MKL_NUM_THREADS', '2')
os.environ.setdefault('VECLIB_MAXIMUM_THREADS', '2')
os.environ.setdefault('NUMEXPR_NUM_THREADS', '2')
os.environ.setdefault('TOKENIZERS_PARALLELISM', 'false')

# Set Python recursion limit to prevent stack overflow
sys.setrecursionlimit(1000)

from app.api.routes import router
from app.core.config import settings
from app.core.logging import app_logger
from app.core.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    app_logger.info("Starting Web Crawler RAG API")
    
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
    return {
        "name": "Web Crawler RAG API",
        "version": "1.0.0",
        "description": "Crawl websites and perform RAG-based question answering",
        "features": [
            "Multi-domain web crawling",
            "PDF processing with OCR",
            "Multilingual support",
            "Vector-based semantic search",
            "RAG with Gemini/DeepSeek LLM",
            "Automatic periodic re-crawling",
            "Detailed source citations"
        ],
        "endpoints": {
            "query": "/api/v1/query",
            "crawl": "/api/v1/crawl",
            "status": "/api/v1/status",
            "health": "/api/v1/health",
            "logs": "/api/v1/logs",
            "stats": "/api/v1/stats"
        }
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        workers=settings.api_workers,
        reload=settings.debug
    )
