"""
Logging configuration using Loguru
"""
import sys
from pathlib import Path
from loguru import logger
from app.core.config import settings


# Track if logging has been configured
_logging_configured = False


def setup_logging(force_reconfigure=False):
    """Configure logging for the application"""
    global _logging_configured
    
    # Only configure once unless forced
    if _logging_configured and not force_reconfigure:
        return logger
    
    # Remove all existing handlers
    logger.remove()
    
    # Console handler
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=settings.log_level,
        colorize=True,
    )
    
    # File handler (only if log_file_path is set)
    if settings.log_file_path:
        log_path = Path(settings.log_file_path)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.add(
            settings.log_file_path,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            level=settings.log_level,
            rotation=settings.log_max_size,
            retention=settings.log_backup_count,
            compression="zip",
            enqueue=True,  # Thread-safe
        )
        
        logger.info(f"Logging configured: {settings.log_file_path}")
    else:
        logger.info("Logging configured: console only")
    
    _logging_configured = True
    
    return logger


# Initialize logger (will use default settings initially)
app_logger = setup_logging()
