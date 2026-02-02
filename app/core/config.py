"""
Configuration management using Pydantic Settings
Supports both .env files and YAML instance configs
"""
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Literal, Optional


class Settings(BaseSettings):
    """Application settings - can be overridden by instance YAML config"""
    
    # Instance Configuration (set by YAML loader)
    instance_name: Optional[str] = Field(default=None, env="INSTANCE_NAME")
    instance_description: Optional[str] = Field(default=None, env="INSTANCE_DESCRIPTION")
    
    # API Configuration
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")
    api_workers: int = Field(default=4, env="API_WORKERS")
    debug: bool = Field(default=False, env="DEBUG")
    
    # LLM API Keys
    gemini_api_key: str = Field(default="", env="GEMINI_API_KEY")
    gemini_model: str = Field(default="gemini-2.0-flash-lite", env="GEMINI_MODEL")
    deepseek_api_key: str = Field(default="", env="DEEPSEEK_API_KEY")
    default_llm_provider: Literal["gemini", "deepseek"] = Field(
        default="gemini", env="DEFAULT_LLM_PROVIDER"
    )
    
    # LLM Configuration
    llm_temperature: float = Field(default=0.7, env="LLM_TEMPERATURE")
    llm_max_tokens: int = Field(default=2048, env="LLM_MAX_TOKENS")
    llm_top_p: float = Field(default=0.9, env="LLM_TOP_P")
    
    # Vector Database Configuration
    vector_db_type: Literal["chromadb", "faiss"] = Field(
        default="chromadb", env="VECTOR_DB_TYPE"
    )
    vector_db_path: str = Field(default="./data/vector_db", env="VECTOR_DB_PATH")
    embedding_model: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2", 
        env="EMBEDDING_MODEL"
    )
    chunk_size: int = Field(default=500, env="CHUNK_SIZE")
    chunk_overlap: int = Field(default=100, env="CHUNK_OVERLAP")
    max_embedding_batch_size: int = Field(default=16, env="MAX_EMBEDDING_BATCH_SIZE")
    chromadb_max_batch_size: int = Field(default=50, env="CHROMADB_MAX_BATCH_SIZE")
    
    # Crawler Configuration
    crawler_concurrent_requests: int = Field(default=1, env="CRAWLER_CONCURRENT_REQUESTS")
    crawler_max_threads: int = Field(default=1, env="CRAWLER_MAX_THREADS")
    crawler_download_delay: int = Field(default=2, env="CRAWLER_DOWNLOAD_DELAY")
    crawler_timeout: int = Field(default=30, env="CRAWLER_TIMEOUT")
    crawler_user_agent: str = Field(
        default="Mozilla/5.0 (compatible; WebCrawlerRAG/1.0)", 
        env="CRAWLER_USER_AGENT"
    )
    max_crawl_depth: int = Field(default=5, env="MAX_CRAWL_DEPTH")
    respect_robots_txt: bool = Field(default=True, env="RESPECT_ROBOTS_TXT")
    enable_sitemap_crawling: bool = Field(default=True, env="ENABLE_SITEMAP_CRAWLING")
    
    # PDF Processing
    enable_ocr: bool = Field(default=True, env="ENABLE_OCR")
    ocr_languages: str = Field(default="eng+ara+hin+urd", env="OCR_LANGUAGES")
    pdf_max_pages: int = Field(default=500, env="PDF_MAX_PAGES")
    
    # Scheduling
    crawl_interval_hours: int = Field(default=24, env="CRAWL_INTERVAL_HOURS")
    enable_background_crawling: bool = Field(default=False, env="ENABLE_BACKGROUND_CRAWLING")
    
    # Database (constructed from instance YAML config)
    database_url: Optional[str] = Field(default=None, env="DATABASE_URL")
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_file_path: Optional[str] = Field(default=None, env="LOG_FILE_PATH")  # Set by instance config
    log_max_size: str = Field(default="100MB", env="LOG_MAX_SIZE")
    log_backup_count: int = Field(default=10, env="LOG_BACKUP_COUNT")
    
    # RAG Configuration
    rag_context_window: int = Field(default=4096, env="RAG_CONTEXT_WINDOW")
    rag_top_k_results: int = Field(default=5, env="RAG_TOP_K_RESULTS")
    rag_similarity_threshold: float = Field(default=0.7, env="RAG_SIMILARITY_THRESHOLD")
    snippet_length: int = Field(default=300, env="SNIPPET_LENGTH")
    
    # Rate Limiting
    rate_limit_requests: int = Field(default=100, env="RATE_LIMIT_REQUESTS")
    rate_limit_period: int = Field(default=60, env="RATE_LIMIT_PERIOD")
    
    # CSV Configuration
    domains_csv_path: str = Field(default="./data/domains.csv", env="DOMAINS_CSV_PATH")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # Allow extra env vars for system libraries (OMP_NUM_THREADS, etc.)


# Global settings instance
settings = Settings()


def reload_settings():
    """Reload settings from environment variables (for multi-instance support)"""
    global settings
    settings = Settings()
    return settings
