"""
Background Scheduler Service
Handles periodic crawling of domains
"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime, timedelta
import pandas as pd
from pathlib import Path
from app.core.config import settings
from app.core.logging import app_logger
from app.services.crawler import WebCrawler
from app.services.vector_db import vector_db
from app.models.database import Domain, CrawledPage
from app.core.database import get_db_context


class CrawlerScheduler:
    """Scheduler for periodic website crawling"""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.is_running = False
    
    def start(self):
        """Start the scheduler"""
        if self.is_running:
            app_logger.warning("Scheduler already running")
            return
        
        if not settings.enable_background_crawling:
            app_logger.info("Background crawling disabled in settings")
            return
        
        # Add job for periodic crawling
        self.scheduler.add_job(
            func=self._periodic_crawl,
            trigger=IntervalTrigger(hours=settings.crawl_interval_hours),
            id='periodic_crawl',
            name='Periodic website crawling',
            replace_existing=True
        )
        
        # Add job for loading domains from CSV
        self.scheduler.add_job(
            func=self._load_domains_from_csv,
            trigger=IntervalTrigger(hours=1),  # Check CSV every hour
            id='load_domains',
            name='Load domains from CSV',
            replace_existing=True
        )
        
        self.scheduler.start()
        self.is_running = True
        
        app_logger.info(
            f"Scheduler started - crawling every {settings.crawl_interval_hours} hours"
        )
        
        # Run initial load and crawl
        self.scheduler.add_job(
            func=self._initial_setup,
            id='initial_setup',
            name='Initial setup'
        )
    
    def stop(self):
        """Stop the scheduler"""
        if not self.is_running:
            return
        
        self.scheduler.shutdown()
        self.is_running = False
        app_logger.info("Scheduler stopped")
    
    async def _initial_setup(self):
        """Initial setup - load domains and start first crawl"""
        app_logger.info("Running initial setup")
        await self._load_domains_from_csv()
        await self._periodic_crawl()
    
    async def _load_domains_from_csv(self):
        """Load domains from CSV file"""
        try:
            csv_path = Path(settings.domains_csv_path)
            
            if not csv_path.exists():
                app_logger.warning(f"Domains CSV not found: {csv_path}")
                # Create example CSV
                self._create_example_csv(csv_path)
                return
            
            # Read CSV
            df = pd.read_csv(csv_path)
            
            if 'domain' not in df.columns:
                app_logger.error("CSV must have 'domain' column")
                return
            
            # Process each domain
            with get_db_context() as db:
                for _, row in df.iterrows():
                    domain = row['domain'].strip()
                    
                    if not domain:
                        continue
                    
                    # Check if domain already exists
                    existing = db.query(Domain).filter(Domain.domain == domain).first()
                    
                    if not existing:
                        # Normalize to base URL
                        if not domain.startswith(('http://', 'https://')):
                            base_url = f'https://{domain}'
                        else:
                            base_url = domain
                        
                        # Create new domain entry
                        new_domain = Domain(
                            domain=domain,
                            base_url=base_url,
                            status='pending',
                            crawl_interval_hours=settings.crawl_interval_hours,
                            next_crawl_at=datetime.utcnow()
                        )
                        db.add(new_domain)
                        app_logger.info(f"Added new domain: {domain}")
            
            app_logger.info(f"Loaded domains from CSV: {csv_path}")
        
        except Exception as e:
            app_logger.error(f"Error loading domains from CSV: {e}")
    
    async def _periodic_crawl(self):
        """Periodic crawling job"""
        app_logger.info("Starting periodic crawl")
        
        try:
            # Get domains that need crawling and extract their data
            domains_to_crawl = []
            with get_db_context() as db:
                now = datetime.utcnow()
                domains = db.query(Domain).filter(
                    Domain.enabled == True,
                    Domain.next_crawl_at <= now
                ).all()
                
                # Extract domain data while still in session
                for domain in domains:
                    domains_to_crawl.append({
                        'id': domain.id,
                        'domain': domain.domain,
                        'crawl_interval_hours': domain.crawl_interval_hours
                    })
            
            if not domains_to_crawl:
                app_logger.info("No domains need crawling at this time")
                return
            
            app_logger.info(f"Crawling {len(domains_to_crawl)} domains")
            
            # Crawl each domain
            async with WebCrawler() as crawler:
                for domain_data in domains_to_crawl:
                    try:
                        # Update status
                        with get_db_context() as db:
                            db_domain = db.query(Domain).filter(
                                Domain.id == domain_data['id']
                            ).first()
                            db_domain.status = 'crawling'
                        
                        # Crawl domain
                        stats = await crawler.crawl_domain(domain_data['domain'])
                        
                        # Update domain record
                        with get_db_context() as db:
                            db_domain = db.query(Domain).filter(
                                Domain.id == domain_data['id']
                            ).first()
                            
                            if 'error' in stats:
                                db_domain.status = 'failed'
                                db_domain.last_error = stats['error']
                                db_domain.error_count += 1
                            else:
                                db_domain.status = 'completed'
                                db_domain.pages_crawled = stats['pages_crawled']
                                db_domain.last_crawl_at = datetime.utcnow()
                                db_domain.error_count = 0
                                db_domain.last_error = None
                            
                            # Set next crawl time
                            db_domain.next_crawl_at = datetime.utcnow() + timedelta(
                                hours=domain_data['crawl_interval_hours']
                            )
                            
                            if not db_domain.first_crawl_at:
                                db_domain.first_crawl_at = datetime.utcnow()
                        
                        # Update vector database
                        if stats.get('pages_crawled', 0) > 0:
                            await self._update_vector_db(domain_data['domain'])
                    
                    except Exception as e:
                        app_logger.error(f"Error crawling domain {domain_data['domain']}: {e}")
                        
                        # Update error in database
                        with get_db_context() as db:
                            db_domain = db.query(Domain).filter(
                                Domain.id == domain_data['id']
                            ).first()
                            db_domain.status = 'failed'
                            db_domain.last_error = str(e)
                            db_domain.error_count += 1
                            db_domain.next_crawl_at = datetime.utcnow() + timedelta(
                                hours=domain_data['crawl_interval_hours']
                            )
            
            app_logger.info("Periodic crawl completed")
        
        except Exception as e:
            app_logger.error(f"Error in periodic crawl: {e}")
    
    async def _update_vector_db(self, domain: str):
        """Update vector database with new/updated pages"""
        try:
            with get_db_context() as db:
                # Get all pages for this domain
                pages = db.query(CrawledPage).filter(
                    CrawledPage.domain == domain
                ).all()
                
                if pages:
                    vector_db.add_documents(pages)
                    app_logger.info(f"Updated vector DB with {len(pages)} pages from {domain}")
        
        except Exception as e:
            app_logger.error(f"Error updating vector DB for {domain}: {e}")
    
    def _create_example_csv(self, csv_path: Path):
        """Create example CSV file"""
        try:
            csv_path.parent.mkdir(parents=True, exist_ok=True)
            
            example_data = {
                'domain': [
                    'example.com',
                    'wikipedia.org',
                ]
            }
            
            df = pd.DataFrame(example_data)
            df.to_csv(csv_path, index=False)
            
            app_logger.info(f"Created example CSV: {csv_path}")
        
        except Exception as e:
            app_logger.error(f"Error creating example CSV: {e}")


# Global scheduler instance
crawler_scheduler = CrawlerScheduler()
