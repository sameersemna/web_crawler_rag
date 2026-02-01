"""
Pydantic models for API requests and responses
"""
from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional, Literal, Dict, Any
from datetime import datetime


class DomainInput(BaseModel):
    """Model for domain input"""
    domain: str = Field(..., description="Domain name to crawl")


class CrawlRequest(BaseModel):
    """Model for manual crawl request"""
    domains: List[str] = Field(..., description="List of domains to crawl")
    force_recrawl: bool = Field(default=False, description="Force recrawl even if recently crawled")


class QueryFilters(BaseModel):
    """Model for query filters"""
    domains: Optional[List[str]] = Field(
        default=None,
        description="Filter by specific domains (e.g., ['example.com', 'docs.example.com'])"
    )
    language: Optional[str] = Field(
        default=None,
        description="Filter by language code (e.g., 'en', 'ar', 'es')"
    )
    content_type: Optional[List[str]] = Field(
        default=None,
        description="Filter by content type (e.g., ['html', 'pdf'])"
    )
    crawled_after: Optional[datetime] = Field(
        default=None,
        description="Only include content crawled after this date"
    )
    crawled_before: Optional[datetime] = Field(
        default=None,
        description="Only include content crawled before this date"
    )
    tags: Optional[List[str]] = Field(
        default=None,
        description="Filter by tags/categories if available"
    )


class RAGQueryRequest(BaseModel):
    """Model for RAG query request"""
    query: str = Field(..., description="Natural language query")
    filters: Optional[QueryFilters] = Field(
        default=None,
        description="Filters to narrow search scope"
    )
    llm_provider: Optional[Literal["gemini", "deepseek"]] = Field(
        default=None, 
        description="LLM provider to use (defaults to system setting)"
    )
    context: Optional[str] = Field(
        default=None, 
        description="Additional context for the query"
    )
    top_k: Optional[int] = Field(
        default=None, 
        description="Number of top results to retrieve (defaults to system setting)"
    )
    snippet_length: Optional[int] = Field(
        default=None,
        description="Length of snippet to return (defaults to system setting)"
    )
    temperature: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=2.0,
        description="LLM temperature for response generation"
    )
    include_sources: bool = Field(
        default=True,
        description="Include source references in response"
    )


class SourceReference(BaseModel):
    """Model for source reference"""
    url: str = Field(..., description="Source URL")
    domain: str = Field(..., description="Domain name")
    title: Optional[str] = Field(None, description="Page/document title")
    snippet: str = Field(..., description="Relevant text snippet from source")
    similarity_score: float = Field(..., description="Similarity score (0-1)")
    page_number: Optional[int] = Field(None, description="Page number if PDF")
    highlighted_text: Optional[str] = Field(None, description="Exact text used for answer")
    content_type: str = Field(..., description="Content type (html, pdf, etc.)")


class RAGQueryResponse(BaseModel):
    """Model for RAG query response"""
    query: str = Field(..., description="Original query")
    answer: str = Field(..., description="Generated answer")
    sources: List[SourceReference] = Field(..., description="Source references")
    llm_provider: str = Field(..., description="LLM provider used")
    confidence_score: Optional[float] = Field(None, description="Confidence score of answer")
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class CrawlStatus(BaseModel):
    """Model for crawl status"""
    domain: str
    status: Literal["pending", "in_progress", "completed", "failed"]
    pages_crawled: int = 0
    last_crawl_time: Optional[datetime] = None
    next_crawl_time: Optional[datetime] = None
    error_message: Optional[str] = None


class CrawlStatusResponse(BaseModel):
    """Model for crawl status response"""
    domains: List[CrawlStatus]
    total_pages_in_db: int
    last_update: datetime


class HealthResponse(BaseModel):
    """Model for health check response"""
    status: str
    version: str
    vector_db_status: str
    llm_providers: dict
    background_crawler: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ErrorResponse(BaseModel):
    """Model for error response"""
    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class CrawlLogEntry(BaseModel):
    """Model for crawl log entry"""
    timestamp: datetime
    domain: str
    url: str
    status: str
    content_type: Optional[str] = None
    size_bytes: Optional[int] = None
    error: Optional[str] = None
