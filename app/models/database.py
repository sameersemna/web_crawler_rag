"""
Database models using SQLAlchemy
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class CrawledPage(Base):
    """Model for crawled pages"""
    __tablename__ = "crawled_pages"
    
    id = Column(Integer, primary_key=True, index=True)
    domain = Column(String, index=True, nullable=False)
    url = Column(String, unique=True, index=True, nullable=False)
    title = Column(String, nullable=True)
    content = Column(Text, nullable=False)
    content_type = Column(String, nullable=False)  # html, pdf, etc.
    size_bytes = Column(Integer, nullable=True)
    crawled_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_modified = Column(DateTime, nullable=True)
    checksum = Column(String, nullable=True)  # For detecting changes
    page_number = Column(Integer, nullable=True)  # For PDF pages
    language = Column(String, nullable=True)
    meta_data = Column(JSON, nullable=True)


class CrawlLog(Base):
    """Model for crawl logs"""
    __tablename__ = "crawl_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True, nullable=False)
    domain = Column(String, index=True, nullable=False)
    url = Column(String, nullable=False)
    status = Column(String, nullable=False)  # success, failed, skipped
    content_type = Column(String, nullable=True)
    size_bytes = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    processing_time_ms = Column(Float, nullable=True)


class Domain(Base):
    """Model for domains"""
    __tablename__ = "domains"
    
    id = Column(Integer, primary_key=True, index=True)
    domain = Column(String, unique=True, index=True, nullable=False)
    base_url = Column(String, nullable=False)
    status = Column(String, nullable=False)  # pending, crawling, completed, failed
    pages_crawled = Column(Integer, default=0)
    first_crawl_at = Column(DateTime, nullable=True)
    last_crawl_at = Column(DateTime, nullable=True)
    next_crawl_at = Column(DateTime, nullable=True)
    crawl_interval_hours = Column(Integer, default=24)
    enabled = Column(Boolean, default=True)
    robots_txt = Column(Text, nullable=True)
    sitemap_urls = Column(JSON, nullable=True)
    error_count = Column(Integer, default=0)
    last_error = Column(Text, nullable=True)
    meta_data = Column(JSON, nullable=True)


class VectorEmbedding(Base):
    """Model for vector embeddings (if not using standalone vector DB)"""
    __tablename__ = "vector_embeddings"
    
    id = Column(Integer, primary_key=True, index=True)
    page_id = Column(Integer, index=True, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    chunk_text = Column(Text, nullable=False)
    vector_id = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)