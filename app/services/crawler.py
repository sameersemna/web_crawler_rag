"""
Web Crawler Service
Handles crawling of websites including HTML pages and PDFs
"""
import asyncio
import hashlib
import ssl
from typing import List, Set, Dict, Optional
from urllib.parse import urljoin, urlparse
from datetime import datetime
import aiohttp
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
from app.core.config import settings
from app.core.logging import app_logger
from app.models.database import CrawledPage, CrawlLog, Domain
from app.core.database import get_db_context
from app.services.pdf_processor import PDFProcessor


class WebCrawler:
    """Web crawler for extracting content from websites"""
    
    def __init__(self):
        self.visited_urls: Set[str] = set()
        self.pdf_processor = PDFProcessor()
        self.session: Optional[aiohttp.ClientSession] = None
        self._approved_domains: Optional[Set[str]] = None  # Cache of approved domains from database
        
    async def __aenter__(self):
        """Async context manager entry"""
        timeout = aiohttp.ClientTimeout(total=settings.crawler_timeout)
        
        # Create SSL context with very lenient settings for maximum compatibility
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        # Allow legacy TLS versions and weaker ciphers for compatibility
        ssl_context.options &= ~ssl.OP_NO_TLSv1
        ssl_context.options &= ~ssl.OP_NO_TLSv1_1
        ssl_context.set_ciphers('DEFAULT@SECLEVEL=1')
        
        # Configure SOCKS5 proxy if provided
        connector = None
        if settings.crawler_socks5_proxy:
            try:
                from aiohttp_socks import ProxyConnector
                app_logger.info(f"Using SOCKS5 proxy: {settings.crawler_socks5_proxy}")
                connector = ProxyConnector.from_url(
                    settings.crawler_socks5_proxy,
                    ssl=ssl_context,
                    limit=settings.crawler_concurrent_requests,
                    limit_per_host=max(2, settings.crawler_concurrent_requests // 4)
                )
            except ImportError:
                app_logger.warning("aiohttp-socks not installed. Install with: pip install aiohttp-socks")
                app_logger.warning("Falling back to direct connection without proxy")
                connector = aiohttp.TCPConnector(
                    ssl=ssl_context,
                    limit=settings.crawler_concurrent_requests,
                    limit_per_host=max(2, settings.crawler_concurrent_requests // 4)
                )
        else:
            # Create TCP connector with SSL context and connection limits
            # Use settings for maximum concurrent connections to control resource usage
            connector = aiohttp.TCPConnector(
                ssl=ssl_context,
                limit=settings.crawler_concurrent_requests,
                limit_per_host=max(2, settings.crawler_concurrent_requests // 4)
            )
        
        self.session = aiohttp.ClientSession(
            timeout=timeout,
            headers={"User-Agent": settings.crawler_user_agent},
            connector=connector
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def _load_approved_domains(self) -> Set[str]:
        """
        Load all approved domains from database
        Returns a set of domain names that are allowed to be crawled
        """
        if self._approved_domains is not None:
            return self._approved_domains
        
        approved = set()
        try:
            with get_db_context() as db:
                domains = db.query(Domain).all()
                for domain in domains:
                    # Normalize domain name (remove www. prefix)
                    normalized = domain.domain.lower().removeprefix('www.')
                    approved.add(normalized)
                    app_logger.debug(f"Approved domain: {normalized}")
            
            self._approved_domains = approved
            app_logger.info(f"Loaded {len(approved)} approved domains for cross-domain crawling")
        except Exception as e:
            app_logger.error(f"Error loading approved domains: {e}")
            self._approved_domains = set()
        
        return self._approved_domains
    
    async def crawl_domain(self, domain: str) -> Dict:
        """
        Crawl a complete domain
        
        Args:
            domain: Domain name to crawl
            
        Returns:
            Dictionary with crawl statistics
        """
        app_logger.info(f"Starting crawl for domain: {domain}")
        
        stats = {
            "domain": domain,
            "pages_crawled": 0,
            "pages_failed": 0,
            "start_time": datetime.utcnow(),
        }
        
        # Ensure session exists
        if not self.session:
            await self.__aenter__()
        
        # Load approved domains for cross-domain crawling
        await self._load_approved_domains()
        
        try:
            # Normalize domain to base URL
            base_url = self._normalize_domain(domain)
            
            # Check robots.txt
            robots_allowed = await self._check_robots_txt(base_url)
            
            # Get sitemap URLs if available
            sitemap_urls = []
            if settings.enable_sitemap_crawling:
                sitemap_urls = await self._get_sitemap_urls(base_url)
                app_logger.info(f"Found {len(sitemap_urls)} URLs in sitemap for {domain}")
            
            # Start crawling from base URL
            urls_to_crawl = {base_url}
            if sitemap_urls:
                urls_to_crawl.update(sitemap_urls)
            
            # Crawl URLs with depth limit
            await self._crawl_urls(
                urls_to_crawl=urls_to_crawl,
                base_url=base_url,
                domain=domain,
                stats=stats,
                max_depth=settings.max_crawl_depth
            )
            
            stats["end_time"] = datetime.utcnow()
            stats["duration_seconds"] = (stats["end_time"] - stats["start_time"]).total_seconds()
            
            app_logger.info(
                f"Completed crawl for {domain}: "
                f"{stats['pages_crawled']} pages crawled, "
                f"{stats['pages_failed']} failed"
            )
            
            return stats
            
        except Exception as e:
            app_logger.error(f"Error crawling domain {domain}: {e}")
            stats["error"] = str(e)
            stats["end_time"] = datetime.utcnow()
            return stats
    
    async def _crawl_urls(
        self,
        urls_to_crawl: Set[str],
        base_url: str,
        domain: str,
        stats: Dict,
        max_depth: int,
        current_depth: int = 0
    ):
        """Recursively crawl URLs"""
        
        if current_depth >= max_depth or not urls_to_crawl:
            return
        
        # Process URLs in batches
        batch_size = settings.crawler_concurrent_requests
        urls_list = list(urls_to_crawl - self.visited_urls)
        
        for i in range(0, len(urls_list), batch_size):
            batch = urls_list[i:i + batch_size]
            
            # Process batch concurrently
            tasks = [
                self._crawl_single_url(url, base_url, domain, stats)
                for url in batch
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Collect new URLs from successfully crawled pages
            new_urls = set()
            for result in results:
                if isinstance(result, set):
                    new_urls.update(result)
            
            # Log how many new URLs were found
            if new_urls:
                app_logger.info(f"Found {len(new_urls)} new URLs at depth {current_depth}")
            else:
                app_logger.info(f"No new URLs found at depth {current_depth}")
            
            # Delay between batches
            if settings.crawler_download_delay > 0:
                await asyncio.sleep(settings.crawler_download_delay)
            
            # Recursively crawl new URLs
            if new_urls and current_depth < max_depth - 1:
                app_logger.info(f"Crawling {len(new_urls)} URLs at depth {current_depth + 1} (max depth: {max_depth})")
                await self._crawl_urls(
                    urls_to_crawl=new_urls,
                    base_url=base_url,
                    domain=domain,
                    stats=stats,
                    max_depth=max_depth,
                    current_depth=current_depth + 1
                )
            elif current_depth >= max_depth - 1:
                app_logger.info(f"Reached max depth {max_depth}, stopping crawl")
    
    async def _crawl_single_url(
        self,
        url: str,
        base_url: str,
        domain: str,
        stats: Dict
    ) -> Set[str]:
        """
        Crawl a single URL
        
        Returns:
            Set of new URLs found on the page
        """
        if url in self.visited_urls:
            return set()
        
        self.visited_urls.add(url)
        new_urls = set()
        log_entry_data = {
            "timestamp": datetime.utcnow(),
            "domain": domain,
            "url": url,
            "status": "pending"
        }
        
        start_time = datetime.utcnow()
        
        try:
            # Try to fetch the URL with retry logic for SSL errors
            response = None
            ssl_retry_attempted = False
            
            try:
                async with self.session.get(url) as response:
                    # Get the final URL after redirects
                    final_url = str(response.url)
                    
                    # If redirected to a different URL, update the URL we're processing
                    if final_url != url:
                        app_logger.info(f"Redirect: {url} -> {final_url}")
                        url = final_url
                        
                        # Add redirected URL to visited set
                        self.visited_urls.add(final_url)
                    
                    content_type = response.headers.get("Content-Type", "").lower()
                    
                    # Handle PDF files
                    if "application/pdf" in content_type:
                        content_data = await response.read()
                        text_content = await self._process_pdf(content_data, url, domain)
                        
                        if text_content:
                            # Extract actual domain from URL (for cross-domain crawling)
                            actual_domain = self._get_domain_from_url(url)
                            await self._save_page(
                                domain=actual_domain,
                                url=url,
                                content=text_content,
                                content_type="pdf",
                                size_bytes=len(content_data)
                            )
                            stats["pages_crawled"] += 1
                            log_entry_data["status"] = "success"
                            log_entry_data["content_type"] = "pdf"
                            log_entry_data["size_bytes"] = len(content_data)
                    
                    # Handle HTML pages
                    elif "text/html" in content_type:
                        html_content = await response.text()
                        soup = BeautifulSoup(html_content, 'lxml')
                        
                        # Extract text content
                        text_content = self._extract_text_from_html(soup)
                        
                        # Extract title
                        title = soup.title.string if soup.title else None
                        
                        # Extract actual domain from URL (for cross-domain crawling)
                        actual_domain = self._get_domain_from_url(url)
                        
                        # Save page
                        await self._save_page(
                            domain=actual_domain,
                            url=url,
                            content=text_content,
                            content_type="html",
                            title=title,
                            size_bytes=len(html_content)
                        )
                        
                        # Extract links using the final URL as base (after redirects)
                        new_urls = self._extract_links(soup, url)
                        
                        # Log the links found
                        app_logger.info(f"Extracted {len(new_urls)} links from {url}")
                        if len(new_urls) > 0 and len(new_urls) <= 5:
                            app_logger.debug(f"Sample links: {list(new_urls)[:5]}")
                        
                        stats["pages_crawled"] += 1
                        log_entry_data["status"] = "success"
                        log_entry_data["content_type"] = "html"
                        log_entry_data["size_bytes"] = len(html_content)
                    
                    else:
                        app_logger.debug(f"Skipping unsupported content type: {content_type} for {url}")
                        log_entry_data["status"] = "skipped"
                        log_entry_data["error_message"] = f"Unsupported content type: {content_type}"
            
            except aiohttp.ClientSSLError as ssl_error:
                # Try with completely disabled SSL verification as fallback
                if not ssl_retry_attempted and url.startswith('https://'):
                    ssl_retry_attempted = True
                    app_logger.warning(f"SSL error on {url}, trying with http fallback")
                    
                    # Try HTTP instead of HTTPS as last resort
                    http_url = url.replace('https://', 'http://')
                    # Also update base_url for link extraction if needed
                    http_base_url = base_url.replace('https://', 'http://') if base_url.startswith('https://') else base_url
                    
                    try:
                        async with self.session.get(http_url) as response:
                            content_type = response.headers.get("Content-Type", "").lower()
                            
                            if "text/html" in content_type:
                                html_content = await response.text()
                                soup = BeautifulSoup(html_content, 'lxml')
                                text_content = self._extract_text_from_html(soup)
                                title = soup.title.string if soup.title else None
                                
                                # Extract actual domain from URL (for cross-domain crawling)
                                actual_domain = self._get_domain_from_url(http_url)
                                
                                await self._save_page(
                                    domain=actual_domain,
                                    url=http_url,
                                    content=text_content,
                                    content_type="html",
                                    title=title,
                                    size_bytes=len(html_content)
                                )
                                
                                # Extract links using HTTP base URL for proper link resolution
                                new_urls = self._extract_links(soup, http_base_url)
                                stats["pages_crawled"] += 1
                                log_entry_data["status"] = "success_http_fallback"
                                log_entry_data["content_type"] = "html"
                                log_entry_data["size_bytes"] = len(html_content)
                                app_logger.info(f"Successfully crawled {http_url} via HTTP fallback, found {len(new_urls)} links")
                                # Don't raise the error since we succeeded with HTTP
                                # The new_urls will be returned normally
                    except Exception as fallback_error:
                        app_logger.error(f"HTTP fallback also failed for {url}: {fallback_error}")
                        raise ssl_error  # Re-raise original SSL error
                else:
                    raise
        
        except aiohttp.ClientSSLError as e:
            error_msg = str(e)
            # Check if it's the specific TLSV1_ALERT_INTERNAL_ERROR
            if "TLSV1_ALERT_INTERNAL_ERROR" in error_msg or "tlsv1 alert internal error" in error_msg:
                app_logger.warning(f"SSL/TLS configuration issue with {url} - server may have incompatible SSL settings")
            else:
                app_logger.error(f"SSL error crawling {url}: {e}")
            stats["pages_failed"] += 1
            log_entry_data["status"] = "ssl_error"
            log_entry_data["error_message"] = f"SSL error: {str(e)}"
        except aiohttp.ClientError as e:
            app_logger.error(f"Client error crawling {url}: {e}")
            stats["pages_failed"] += 1
            log_entry_data["status"] = "failed"
            log_entry_data["error_message"] = f"Client error: {str(e)}"
        except Exception as e:
            app_logger.error(f"Error crawling {url}: {e}")
            stats["pages_failed"] += 1
            log_entry_data["status"] = "failed"
            log_entry_data["error_message"] = str(e)
        
        # Log the crawl
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        log_entry_data["processing_time_ms"] = processing_time
        await self._log_crawl(log_entry_data)
        
        return new_urls
    
    async def _process_pdf(self, pdf_data: bytes, url: str, domain: str) -> str:
        """Process PDF file and extract text"""
        try:
            return await self.pdf_processor.extract_text(pdf_data, url)
        except Exception as e:
            app_logger.error(f"Error processing PDF {url}: {e}")
            return ""
    
    def _extract_text_from_html(self, soup: BeautifulSoup) -> str:
        """Extract clean text from HTML"""
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()
        
        # Get text
        text = soup.get_text(separator=' ', strip=True)
        
        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        return text
    
    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> Set[str]:
        """Extract and normalize links from HTML"""
        links = set()
        external_frames = []
        
        # Extract regular anchor links
        all_anchors = soup.find_all('a', href=True)
        app_logger.debug(f"Found {len(all_anchors)} anchor tags in HTML from {base_url}")
        
        skipped_count = 0
        different_domain_count = 0
        cross_domain_approved_count = 0
        
        for link in all_anchors:
            href = link['href']
            
            # Skip anchors, mailto, javascript, etc.
            if href.startswith(('#', 'mailto:', 'javascript:', 'tel:')):
                skipped_count += 1
                continue
            
            # Convert relative URLs to absolute
            absolute_url = urljoin(base_url, href)
            
            # Include URLs from the same domain
            if self._is_same_domain(absolute_url, base_url):
                # Remove fragments
                absolute_url = absolute_url.split('#')[0]
                links.add(absolute_url)
            # Also include URLs from other approved domains in domains.csv
            elif self._is_approved_domain(absolute_url):
                absolute_url = absolute_url.split('#')[0]
                links.add(absolute_url)
                cross_domain_approved_count += 1
                if cross_domain_approved_count <= 5:
                    app_logger.info(f"Including cross-domain link from approved domain: {absolute_url}")
            else:
                different_domain_count += 1
                if different_domain_count <= 3:
                    app_logger.debug(f"Skipping different domain: {absolute_url} vs {base_url}")
        
        if cross_domain_approved_count > 0:
            app_logger.info(f"Link extraction from {base_url}: {len(all_anchors)} anchors found, {skipped_count} skipped (mailto/javascript/etc), {cross_domain_approved_count} cross-domain approved links, {different_domain_count} different domain, {len(links)} total links")
        else:
            app_logger.info(f"Link extraction from {base_url}: {len(all_anchors)} anchors found, {skipped_count} skipped (mailto/javascript/etc), {different_domain_count} different domain, {len(links)} same-domain links")
        if len(links) > 0:
            app_logger.debug(f"Same-domain links: {list(links)[:5]}")
        
        # Extract frame and iframe sources
        for frame in soup.find_all(['frame', 'iframe'], src=True):
            src = frame['src']
            
            # Skip data URIs and javascript
            if src.startswith(('data:', 'javascript:', 'about:')):
                continue
            
            # Convert relative URLs to absolute
            absolute_url = urljoin(base_url, src)
            
            # Check if same domain
            if self._is_same_domain(absolute_url, base_url):
                # Remove fragments
                absolute_url = absolute_url.split('#')[0]
                links.add(absolute_url)
            else:
                # Log external frame - this might be legitimate content
                external_frames.append(absolute_url)
        
        # Log external frames found
        if external_frames:
            app_logger.info(
                f"Found {len(external_frames)} external frame(s) on {base_url}: "
                f"{', '.join(external_frames[:3])}{'...' if len(external_frames) > 3 else ''}"
            )
        
        return links
    
    async def _check_robots_txt(self, base_url: str) -> bool:
        """Check robots.txt for crawling permissions"""
        if not settings.respect_robots_txt:
            return True
        
        robots_url = urljoin(base_url, "/robots.txt")
        
        try:
            async with self.session.get(robots_url) as response:
                if response.status == 200:
                    robots_content = await response.text()
                    # Simple check - in production, use robotparser
                    if "Disallow: /" in robots_content:
                        app_logger.warning(f"Robots.txt disallows crawling for {base_url}")
                        return False
                return True
        except Exception:
            # If robots.txt doesn't exist or error, allow crawling
            return True
    
    async def _get_sitemap_urls(self, base_url: str) -> List[str]:
        """Extract URLs from sitemap.xml"""
        sitemap_urls = []
        sitemap_locations = [
            "/sitemap.xml",
            "/sitemap_index.xml",
            "/sitemap-index.xml"
        ]
        
        for sitemap_path in sitemap_locations:
            sitemap_url = urljoin(base_url, sitemap_path)
            
            try:
                async with self.session.get(sitemap_url) as response:
                    if response.status == 200:
                        content = await response.text()
                        urls = self._parse_sitemap(content)
                        sitemap_urls.extend(urls)
                        app_logger.info(f"Found sitemap at {sitemap_url} with {len(urls)} URLs")
                        break
            except Exception as e:
                app_logger.debug(f"No sitemap found at {sitemap_url}: {e}")
                continue
        
        return sitemap_urls
    
    def _parse_sitemap(self, sitemap_content: str) -> List[str]:
        """Parse sitemap XML and extract URLs"""
        urls = []
        
        try:
            root = ET.fromstring(sitemap_content)
            
            # Handle different sitemap namespaces
            namespaces = {
                'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9',
                '': 'http://www.sitemaps.org/schemas/sitemap/0.9'
            }
            
            # Extract URLs
            for url_elem in root.findall('.//sm:loc', namespaces) or root.findall('.//loc'):
                url = url_elem.text
                if url:
                    urls.append(url.strip())
        
        except Exception as e:
            app_logger.error(f"Error parsing sitemap: {e}")
        
        return urls
    
    def _normalize_domain(self, domain: str) -> str:
        """Normalize domain to base URL"""
        if not domain.startswith(('http://', 'https://')):
            domain = f'https://{domain}'
        
        parsed = urlparse(domain)
        return f"{parsed.scheme}://{parsed.netloc}"
    
    def _is_same_domain(self, url: str, base_url: str) -> bool:
        """Check if URL belongs to the same domain or any subdomain"""
        url_netloc = urlparse(url).netloc.lower()
        base_netloc = urlparse(base_url).netloc.lower()
        
        # Remove www. prefix from base domain for matching
        base_domain = base_netloc.removeprefix('www.')
        url_domain = url_netloc.removeprefix('www.')
        
        # Check if same domain or subdomain
        # Examples: 
        # - bakkah.net == bakkah.net ✓
        # - blog.bakkah.net ends with .bakkah.net ✓
        # - api.shop.bakkah.net ends with .bakkah.net ✓
        return url_domain == base_domain or url_domain.endswith('.' + base_domain)
    
    def _is_approved_domain(self, url: str) -> bool:
        """
        Check if URL belongs to any approved domain from domains.csv
        Returns True if the URL's domain matches any domain in the database
        """
        if self._approved_domains is None:
            return False
        
        url_netloc = urlparse(url).netloc.lower()
        url_domain = url_netloc.removeprefix('www.')
        
        # Check if URL's base domain is in approved list
        for approved_domain in self._approved_domains:
            # Check exact match or subdomain
            if url_domain == approved_domain or url_domain.endswith('.' + approved_domain):
                return True
        
        return False
    
    def _get_domain_from_url(self, url: str) -> str:
        """Extract domain name from URL"""
        netloc = urlparse(url).netloc.lower()
        return netloc.removeprefix('www.')
    
    async def _save_page(
        self,
        domain: str,
        url: str,
        content: str,
        content_type: str,
        title: Optional[str] = None,
        size_bytes: Optional[int] = None,
        page_number: Optional[int] = None
    ):
        """Save crawled page to database and queue for embedding"""
        page_id = None
        needs_embedding = False
        
        with get_db_context() as db:
            # Calculate checksum
            checksum = hashlib.md5(content.encode()).hexdigest()
            
            # Check if page already exists
            existing_page = db.query(CrawledPage).filter(
                CrawledPage.url == url
            ).first()
            
            if existing_page:
                # Update if content changed
                if existing_page.checksum != checksum:
                    existing_page.content = content
                    existing_page.checksum = checksum
                    existing_page.crawled_at = datetime.utcnow()
                    existing_page.size_bytes = size_bytes
                    db.flush()  # Ensure ID is available
                    page_id = existing_page.id
                    needs_embedding = True
                    app_logger.debug(f"Updated page: {url}")
            else:
                # Create new page
                page = CrawledPage(
                    domain=domain,
                    url=url,
                    title=title,
                    content=content,
                    content_type=content_type,
                    size_bytes=size_bytes,
                    checksum=checksum,
                    page_number=page_number,
                    crawled_at=datetime.utcnow()
                )
                db.add(page)
                db.flush()  # Ensure ID is available
                page_id = page.id
                needs_embedding = True
                app_logger.debug(f"Saved new page: {url}")
        
        # Queue page for async embedding (outside DB transaction)
        if needs_embedding and page_id:
            try:
                from app.services.embedding_queue import embedding_queue
                await embedding_queue.enqueue_page(page_id)
            except Exception as e:
                app_logger.warning(f"Failed to queue page for embedding: {e}")
    
    async def _log_crawl(self, log_data: Dict):
        """Log crawl activity"""
        with get_db_context() as db:
            log_entry = CrawlLog(**log_data)
            db.add(log_entry)
