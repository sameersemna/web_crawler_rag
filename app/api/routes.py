"""
Main API Routes
"""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from app.models.schemas import (
    RAGQueryRequest, RAGQueryResponse, CrawlRequest,
    CrawlStatusResponse, CrawlStatus, HealthResponse, ErrorResponse
)
from app.services.rag_service import rag_service
from app.services.crawler import WebCrawler
from app.services.vector_db import vector_db
from app.services.llm_service import llm_service
from app.services.scheduler import crawler_scheduler
from app.services.resource_monitor import resource_monitor
from app.core.database import get_db
from app.models.database import Domain, CrawledPage, CrawlLog
from app.core.logging import app_logger
from app.core.config import settings

router = APIRouter()


@router.post("/query", response_model=RAGQueryResponse)
async def query_rag(request: RAGQueryRequest):
    """
    Query the RAG system
    
    Process a natural language query and return an answer based on crawled website data
    
    ⚠️ WARNING: Large collections (30k+ docs) may cause crashes.
    For better stability, use /query-filtered with domain filters.
    """
    try:
        response = await rag_service.query(request)
        return response
    except Exception as e:
        app_logger.error(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query-filtered", response_model=RAGQueryResponse)
async def query_rag_filtered(request: RAGQueryRequest):
    """
    Query with REQUIRED domain filtering (safer for large collections)
    
    Forces queries to search only specific domains, preventing crashes on large collections.
    
    Example:
    {
        "query": "what courses do you offer?",
        "top_k": 3,
        "filters": {
            "domains": ["spubs.com", "rabee.co.uk"]
        }
    }
    """
    try:
        # Enforce domain filtering
        if not request.filters or not request.filters.domains:
            raise HTTPException(
                status_code=400,
                detail="Domain filter is required for filtered queries. Specify 'filters.domains' in request."
            )
        
        response = await rag_service.query(request)
        return response
    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(f"Error processing filtered query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/crawl")
async def trigger_crawl(
    request: CrawlRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Trigger manual crawl of domains
    
    Start crawling the specified domains immediately
    """
    try:
        # Validate domains exist or create them
        for domain_name in request.domains:
            domain = db.query(Domain).filter(Domain.domain == domain_name).first()
            
            if not domain:
                # Create new domain
                base_url = domain_name if domain_name.startswith('http') else f'https://{domain_name}'
                domain = Domain(
                    domain=domain_name,
                    base_url=base_url,
                    status='pending',
                    next_crawl_at=datetime.utcnow()
                )
                db.add(domain)
        
        db.commit()
        
        # Start crawl in background
        background_tasks.add_task(
            _background_crawl,
            request.domains,
            request.force_recrawl
        )
        
        return {
            "message": f"Crawl started for {len(request.domains)} domain(s)",
            "domains": request.domains
        }
    
    except Exception as e:
        app_logger.error(f"Error triggering crawl: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/embed")
async def trigger_embed(
    request: CrawlRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Trigger embedding of already-crawled pages without re-crawling
    
    This will take existing pages from the database and add them to the vector database
    """
    try:
        # Validate domains exist
        for domain_name in request.domains:
            domain = db.query(Domain).filter(Domain.domain == domain_name).first()
            
            if not domain:
                raise HTTPException(
                    status_code=404, 
                    detail=f"Domain {domain_name} not found. Please crawl it first using /crawl endpoint."
                )
        
        # Start embedding in background
        background_tasks.add_task(
            _background_embed,
            request.domains
        )
        
        return {
            "message": f"Embedding started for {len(request.domains)} domain(s)",
            "domains": request.domains
        }
    
    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(f"Error triggering embed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status", response_model=CrawlStatusResponse)
async def get_crawl_status(db: Session = Depends(get_db)):
    """
    Get crawl status for all domains
    
    Returns current status, pages crawled, and next crawl time for each domain
    """
    try:
        domains = db.query(Domain).all()
        
        domain_statuses = []
        for domain in domains:
            status = CrawlStatus(
                domain=domain.domain,
                status=domain.status,
                pages_crawled=domain.pages_crawled,
                last_crawl_time=domain.last_crawl_at,
                next_crawl_time=domain.next_crawl_at,
                error_message=domain.last_error
            )
            domain_statuses.append(status)
        
        # Get total pages in database
        total_pages = db.query(CrawledPage).count()
        
        return CrawlStatusResponse(
            domains=domain_statuses,
            total_pages_in_db=total_pages,
            last_update=datetime.utcnow()
        )
    
    except Exception as e:
        app_logger.error(f"Error getting crawl status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint
    
    Returns system status and available services
    """
    try:
        # Check vector DB
        try:
            vector_stats = vector_db.get_stats()
            vector_db_status = "healthy"
        except Exception:
            vector_db_status = "unhealthy"
        
        # Check LLM providers
        llm_providers = {
            "gemini": llm_service.check_provider_availability("gemini"),
            "deepseek": llm_service.check_provider_availability("deepseek")
        }
        
        # Check scheduler
        scheduler_status = "running" if crawler_scheduler.is_running else "stopped"
        
        return HealthResponse(
            status="healthy",
            version="1.0.0",
            vector_db_status=vector_db_status,
            llm_providers=llm_providers,
            background_crawler=scheduler_status
        )
    
    except Exception as e:
        app_logger.error(f"Error in health check: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/resources")
async def get_resource_usage():
    """
    Get current resource usage (memory, CPU, threads)
    
    Use this to monitor if the application is consuming too many resources
    """
    try:
        status = resource_monitor.get_status()
        return status
    except Exception as e:
        app_logger.error(f"Error getting resource usage: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/logs")
async def get_crawl_logs(
    limit: int = 100,
    domain: str = None,
    db: Session = Depends(get_db)
):
    """
    Get crawl logs
    
    Returns recent crawl activity logs, optionally filtered by domain
    """
    try:
        query = db.query(CrawlLog).order_by(CrawlLog.timestamp.desc())
        
        if domain:
            query = query.filter(CrawlLog.domain == domain)
        
        logs = query.limit(limit).all()
        
        return {
            "logs": [
                {
                    "timestamp": log.timestamp,
                    "domain": log.domain,
                    "url": log.url,
                    "status": log.status,
                    "content_type": log.content_type,
                    "size_bytes": log.size_bytes,
                    "error_message": log.error_message,
                    "processing_time_ms": log.processing_time_ms
                }
                for log in logs
            ],
            "total": len(logs)
        }
    
    except Exception as e:
        app_logger.error(f"Error getting logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/domain/{domain_name}")
async def delete_domain(domain_name: str, db: Session = Depends(get_db)):
    """
    Delete a domain and all its crawled data
    
    Removes domain, crawled pages, and vector embeddings
    """
    try:
        # Get domain
        domain = db.query(Domain).filter(Domain.domain == domain_name).first()
        
        if not domain:
            raise HTTPException(status_code=404, detail="Domain not found")
        
        # Delete crawled pages
        pages = db.query(CrawledPage).filter(CrawledPage.domain == domain_name).all()
        
        for page in pages:
            # Delete from vector DB
            vector_db.delete_document(page.url)
        
        # Delete from database
        db.query(CrawledPage).filter(CrawledPage.domain == domain_name).delete()
        db.query(CrawlLog).filter(CrawlLog.domain == domain_name).delete()
        db.delete(domain)
        db.commit()
        
        app_logger.info(f"Deleted domain: {domain_name}")
        
        return {"message": f"Domain {domain_name} deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(f"Error deleting domain: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_statistics(db: Session = Depends(get_db)):
    """
    Get system statistics
    
    Returns overall statistics about crawled data and system usage
    """
    try:
        # Database stats
        total_domains = db.query(Domain).count()
        active_domains = db.query(Domain).filter(Domain.enabled == True).count()
        total_pages = db.query(CrawledPage).count()
        total_logs = db.query(CrawlLog).count()
        
        # Vector DB stats
        vector_stats = vector_db.get_stats()
        
        # Recent activity
        recent_crawls = db.query(CrawlLog).filter(
            CrawlLog.status == 'success'
        ).order_by(CrawlLog.timestamp.desc()).limit(10).all()
        
        return {
            "domains": {
                "total": total_domains,
                "active": active_domains
            },
            "pages": {
                "total": total_pages
            },
            "vector_db": vector_stats,
            "logs": {
                "total": total_logs
            },
            "recent_crawls": [
                {
                    "domain": log.domain,
                    "url": log.url,
                    "timestamp": log.timestamp
                }
                for log in recent_crawls
            ]
        }
    
    except Exception as e:
        app_logger.error(f"Error getting statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def _background_crawl(domains: List[str], force_recrawl: bool):
    """Background task for crawling"""
    try:
        async with WebCrawler() as crawler:
            for domain in domains:
                app_logger.info(f"Background crawl started for: {domain}")
                stats = await crawler.crawl_domain(domain)
                
                app_logger.info(f"Crawl completed with stats: {stats.get('pages_crawled', 0)} pages crawled")
                
                # Update vector database - always try regardless of stats
                try:
                    with get_db_context() as db:
                        pages = db.query(CrawledPage).filter(
                            CrawledPage.domain == domain
                        ).all()
                        
                        app_logger.info(f"Found {len(pages)} pages in database for {domain}")
                        
                        if pages:
                            app_logger.info(f"Starting to add {len(pages)} pages to vector database...")
                            vector_db.add_documents(pages)
                            app_logger.info(f"Successfully completed adding pages to vector database")
                        else:
                            app_logger.warning(f"No pages found in database for {domain}")
                
                except Exception as e:
                    app_logger.error(f"Error adding documents to vector DB for {domain}: {e}", exc_info=True)
    
    except Exception as e:
        app_logger.error(f"Error in background crawl: {e}", exc_info=True)


async def _background_embed(domains: List[str]):
    """Background task for embedding existing crawled pages without re-crawling"""
    try:
        for domain in domains:
            app_logger.info(f"Background embedding started for: {domain}")
            
            try:
                with get_db_context() as db:
                    pages = db.query(CrawledPage).filter(
                        CrawledPage.domain == domain
                    ).all()
                    
                    app_logger.info(f"Found {len(pages)} pages in database for {domain}")
                    
                    if pages:
                        app_logger.info(f"Starting to add {len(pages)} pages to vector database...")
                        vector_db.add_documents(pages)
                        app_logger.info(f"Successfully completed adding pages to vector database for {domain}")
                    else:
                        app_logger.warning(f"No pages found in database for {domain}")
            
            except Exception as e:
                app_logger.error(f"Error adding documents to vector DB for {domain}: {e}", exc_info=True)
    
    except Exception as e:
        app_logger.error(f"Error in background embed: {e}", exc_info=True)


# Import get_db_context for background task
from app.core.database import get_db_context
