"""
Background Crawler Service
Runs automatic scheduled crawling independently from the API server
"""
import os
import sys
import asyncio
import signal

# Set resource limits BEFORE importing other modules
os.environ.setdefault('OMP_NUM_THREADS', '2')
os.environ.setdefault('OPENBLAS_NUM_THREADS', '2')
os.environ.setdefault('MKL_NUM_THREADS', '2')
os.environ.setdefault('VECLIB_MAXIMUM_THREADS', '2')
os.environ.setdefault('NUMEXPR_NUM_THREADS', '2')
os.environ.setdefault('TOKENIZERS_PARALLELISM', 'false')

# Set Python recursion limit to prevent stack overflow
sys.setrecursionlimit(1000)

from app.core.config import settings
from app.core.logging import app_logger
from app.core.database import init_db
from app.services.scheduler import crawler_scheduler


class CrawlerService:
    """Background crawler service"""
    
    def __init__(self):
        self.running = False
        self._setup_signal_handlers()
    
    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        app_logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        self.stop()
    
    def start(self):
        """Start the crawler service"""
        app_logger.info("=" * 60)
        app_logger.info("Starting Background Crawler Service")
        app_logger.info("=" * 60)
        
        if not settings.enable_background_crawling:
            app_logger.warning("Background crawling is DISABLED in .env")
            app_logger.warning("Set ENABLE_BACKGROUND_CRAWLING=True to enable")
            app_logger.info("Service will exit now.")
            return
        
        # Initialize database
        app_logger.info("Initializing database...")
        init_db()
        
        # Start scheduler
        app_logger.info("Starting crawler scheduler...")
        crawler_scheduler.start()
        
        self.running = True
        app_logger.info("=" * 60)
        app_logger.info("Background Crawler Service is now running")
        app_logger.info(f"Crawl interval: {settings.crawl_interval_hours} hours")
        app_logger.info(f"Crawl depth: {settings.max_crawl_depth}")
        app_logger.info(f"Domains CSV: {settings.domains_csv_path}")
        app_logger.info("Press Ctrl+C to stop")
        app_logger.info("=" * 60)
        
        # Keep the service running
        try:
            # Run the asyncio event loop
            loop = asyncio.get_event_loop()
            loop.run_forever()
        except KeyboardInterrupt:
            app_logger.info("Received keyboard interrupt")
        finally:
            self.stop()
    
    def stop(self):
        """Stop the crawler service"""
        if not self.running:
            return
        
        app_logger.info("Stopping Background Crawler Service...")
        crawler_scheduler.stop()
        self.running = False
        app_logger.info("Background Crawler Service stopped")
        
        # Stop the event loop
        loop = asyncio.get_event_loop()
        loop.stop()


def main():
    """Main entry point"""
    service = CrawlerService()
    service.start()


if __name__ == "__main__":
    main()
