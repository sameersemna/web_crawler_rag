"""
Background Crawler Service with Multi-Instance Support
Runs automatic scheduled crawling independently from the API server
Usage: python main_crawl.py [config_file.yaml]
"""
import os
import sys
import asyncio
import signal
import argparse
from pathlib import Path

# AUTO-DETECT and apply optimal resource configuration BEFORE importing other modules
from app.utils.resource_detector import ResourceDetector
optimal_config = ResourceDetector.get_optimal_config()
ResourceDetector.apply_config(optimal_config)

# Set additional environment variables
os.environ.setdefault('TOKENIZERS_PARALLELISM', 'false')

# Set Python recursion limit to prevent stack overflow
sys.setrecursionlimit(1000)

from app.core.config import settings, reload_settings
from app.core.config_loader import load_instance_config
from app.core.logging import app_logger, setup_logging
from app.core.database import init_db, initialize_database
from app.services.scheduler import crawler_scheduler
from app.services.embedding_queue import embedding_queue


# Parse command line arguments
def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Background Crawler Service with multi-instance support'
    )
    parser.add_argument(
        'config',
        nargs='?',
        default=None,
        help='YAML configuration file (e.g., islam.yaml, law.yaml)'
    )
    return parser.parse_args()


class CrawlerService:
    """Background crawler service"""
    
    def __init__(self):
        self.running = False
        self.shutdown_event = None
        self._setup_signal_handlers()
    
    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        app_logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        self.running = False
    
    def start(self):
        """Start the crawler service"""
        asyncio.run(self._async_start())
    
    async def _async_start(self):
        """Async initialization and startup"""
        instance_name = getattr(settings, 'instance_name', 'default')
        
        app_logger.info("=" * 60)
        app_logger.info(f"Starting Background Crawler Service - Instance: {instance_name}")
        app_logger.info("=" * 60)
        
        if not settings.enable_background_crawling:
            app_logger.warning("Background crawling is DISABLED")
            app_logger.warning("Set 'crawler.enable_background: true' in YAML config")
            app_logger.info("Service will exit now.")
            return
        
        # Initialize database
        app_logger.info("Initializing database...")
        init_db()
        
        # Start embedding queue (processes embeddings in parallel)
        await embedding_queue.start()
        
        # Start scheduler
        app_logger.info("Starting crawler scheduler...")
        crawler_scheduler.start()
        
        self.running = True
        app_logger.info("=" * 60)
        app_logger.info("Background Crawler Service is now running")
        app_logger.info(f"Instance: {instance_name}")
        app_logger.info(f"Crawl interval: {settings.crawl_interval_hours} hours")
        app_logger.info(f"Crawl depth: {settings.max_crawl_depth}")
        app_logger.info(f"Domains CSV: {settings.domains_csv_path}")
        app_logger.info(f"Database: {settings.database_url}")
        app_logger.info(f"Async embeddings: ENABLED (GPU+Network in parallel)")
        app_logger.info("Press Ctrl+C to stop")
        app_logger.info("=" * 60)
        
        # Keep the service running - wait indefinitely
        try:
            while self.running:
                await asyncio.sleep(0.5)  # Shorter sleep for faster shutdown response
        except (KeyboardInterrupt, asyncio.CancelledError):
            app_logger.info("Received shutdown signal")
        finally:
            app_logger.info("Shutting down services...")
            await self._async_stop()
    
    async def _async_stop(self):
        """Stop the crawler service (async)"""
        app_logger.info("Stopping Background Crawler Service...")
        
        self.running = False
        
        # Stop embedding queue first (process remaining items)
        try:
            await asyncio.wait_for(embedding_queue.stop(), timeout=30.0)
        except asyncio.TimeoutError:
            app_logger.warning("Embedding queue stop timed out after 30s")
        
        # Stop scheduler
        try:
            crawler_scheduler.stop()
        except Exception as e:
            app_logger.error(f"Error stopping scheduler: {e}")
        
        app_logger.info("Background Crawler Service stopped")


def main():
    """Main entry point"""
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
        
        # Set environment variables
        os.environ['INSTANCE_NAME'] = instance_cfg.instance_name
        os.environ['INSTANCE_DESCRIPTION'] = instance_cfg.instance_description
        os.environ['DATABASE_URL'] = f"sqlite:///{instance_cfg.db_path}"
        os.environ['VECTOR_DB_PATH'] = str(instance_cfg.vector_db_path)
        os.environ['DOMAINS_CSV_PATH'] = str(instance_cfg.domains_file)
        
        # Reload settings from updated environment variables
        reload_settings()
        
        # Override settings with instance config
        settings.instance_name = instance_cfg.instance_name
        settings.instance_description = instance_cfg.instance_description
        settings.database_url = f"sqlite:///{instance_cfg.db_path}"
        settings.vector_db_path = str(instance_cfg.vector_db_path)
        settings.domains_csv_path = str(instance_cfg.domains_file)
        
        # Construct log file path from data_dir (not from env)
        settings.log_file_path = str(instance_cfg.logs_dir / "crawler.log")
        
        # Override crawler settings
        settings.max_crawl_depth = instance_cfg.get('crawler.max_depth', 5)
        settings.crawler_concurrent_requests = instance_cfg.get('crawler.concurrent_requests', 2)
        settings.crawler_download_delay = instance_cfg.get('crawler.download_delay', 1.0)
        settings.crawler_user_agent = instance_cfg.get('crawler.user_agent', 'WebCrawlerBot/1.0')
        socks5_proxy = instance_cfg.get('crawler.socks5_proxy', '')
        settings.crawler_socks5_proxy = socks5_proxy if socks5_proxy else None
        settings.enable_background_crawling = instance_cfg.get('crawler.enable_background', False)
        settings.crawl_interval_hours = 24  # Default to 24 hours
        
        # Parse schedule if provided
        schedule = instance_cfg.get('crawler.schedule')
        if schedule:
            app_logger.info(f"Crawl schedule: {schedule}")
        
        # Override embedding settings
        settings.embedding_model = instance_cfg.get('embeddings.model', 'sentence-transformers/all-MiniLM-L6-v2')
        settings.chunk_size = instance_cfg.get('embeddings.chunk_size', 500)
        settings.chunk_overlap = instance_cfg.get('embeddings.chunk_overlap', 100)
        settings.max_embedding_batch_size = instance_cfg.get('embeddings.batch_size', 32)
        settings.chromadb_max_batch_size = instance_cfg.get('embeddings.chromadb_batch_size', 100)
        
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
        print(f"Starting Background Crawler - Instance: {instance_cfg.instance_name}")
        print(f"{'='*60}")
        print(f"Description: {instance_cfg.instance_description}")
        print(f"Data directory: {instance_cfg.data_dir}")
        print(f"Database: {instance_cfg.db_path}")
        print(f"Domains file: {instance_cfg.domains_file}")
        print(f"Log file: {instance_cfg.logs_dir / 'crawler.log'}")
        print(f"Crawl depth: {settings.max_crawl_depth}")
        print(f"Background crawling: {settings.enable_background_crawling}")
        print(f"{'='*60}\n")
    else:
        print("\nNo configuration file specified. Using default settings.")
        print("Usage: python main_crawl.py <config_file.yaml>")
        print("\nExample:")
        print("  python main_crawl.py islam.yaml")
        print("  python main_crawl.py law.yaml\n")
    
    service = CrawlerService()
    service.start()


if __name__ == "__main__":
    main()
