"""
Async Embedding Queue Service
Processes embeddings in background while crawling continues
"""
import asyncio
from typing import List, Set
from app.core.logging import app_logger
from app.models.database import CrawledPage
from app.services.vector_db import vector_db
from app.core.database import get_db_context


class EmbeddingQueue:
    """
    Background queue that processes embeddings asynchronously
    Allows crawling and embedding to happen in parallel
    """
    
    def __init__(self, batch_size: int = 10, batch_timeout: float = 5.0):
        """
        Args:
            batch_size: Number of pages to batch before processing
            batch_timeout: Max seconds to wait before processing incomplete batch
        """
        self.queue = asyncio.Queue()
        self.batch_size = batch_size
        self.batch_timeout = batch_timeout
        self.is_running = False
        self.worker_task = None
        self.processed_count = 0
        self.failed_count = 0
        self._processed_ids: Set[int] = set()  # Track processed page IDs
        
    async def start(self):
        """Start the background worker"""
        if self.is_running:
            app_logger.warning("Embedding queue already running")
            return
        
        self.is_running = True
        self.worker_task = asyncio.create_task(self._worker())
        app_logger.info("✓ Embedding queue started - processing embeddings in parallel with crawling")
    
    async def stop(self):
        """Stop the background worker and process remaining items"""
        if not self.is_running:
            return
        
        app_logger.info("Stopping embedding queue...")
        self.is_running = False
        
        # Wait for worker to finish processing remaining items
        if self.worker_task:
            try:
                # Give it 20 seconds to finish processing
                await asyncio.wait_for(self.worker_task, timeout=20.0)
            except asyncio.TimeoutError:
                app_logger.warning("Embedding worker did not finish in time, cancelling...")
                self.worker_task.cancel()
                try:
                    await self.worker_task
                except asyncio.CancelledError:
                    pass
        
        app_logger.info(f"Embedding queue stopped. Processed: {self.processed_count}, Failed: {self.failed_count}, Remaining: {self.queue.qsize()}\")")
    
    async def enqueue_page(self, page_id: int):
        """
        Add a page ID to the embedding queue
        
        Args:
            page_id: Database ID of the CrawledPage to process
        """
        if page_id not in self._processed_ids:
            await self.queue.put(page_id)
    
    async def enqueue_pages(self, page_ids: List[int]):
        """
        Add multiple page IDs to the embedding queue
        
        Args:
            page_ids: List of database IDs of CrawledPages to process
        """
        for page_id in page_ids:
            if page_id not in self._processed_ids:
                await self.queue.put(page_id)
    
    async def _worker(self):
        """Background worker that processes embedding batches"""
        app_logger.info("Embedding worker started")
        
        try:
            while self.is_running or not self.queue.empty():
                batch = []
                
                try:
                    # Collect batch with timeout
                    timeout_start = asyncio.get_event_loop().time()
                    
                    while len(batch) < self.batch_size:
                        remaining_time = self.batch_timeout - (asyncio.get_event_loop().time() - timeout_start)
                        
                        if remaining_time <= 0:
                            break
                        
                        # If we're stopping and queue is empty, break
                        if not self.is_running and self.queue.empty():
                            break
                        
                        try:
                            page_id = await asyncio.wait_for(
                                self.queue.get(),
                                timeout=min(remaining_time, 1.0)  # Max 1s wait to check is_running
                            )
                            batch.append(page_id)
                        except asyncio.TimeoutError:
                            # Check if we should stop
                            if not self.is_running:
                                break
                            continue
                    
                    # Process batch if we have items
                    if batch:
                        await self._process_batch(batch)
                    
                    # If not running and no items, exit
                    if not self.is_running and not batch:
                        break
                    
                except Exception as e:
                    app_logger.error(f"Error in embedding worker: {e}", exc_info=True)
                    await asyncio.sleep(1)  # Prevent tight loop on error
        
        except asyncio.CancelledError:
            app_logger.info("Embedding worker cancelled")
            raise
        finally:
            app_logger.info("Embedding worker stopped")
    
    async def _process_batch(self, page_ids: List[int]):
        """
        Process a batch of pages for embedding
        
        Args:
            page_ids: List of CrawledPage IDs to process
        """
        max_retries = 3
        retry_delay = 1.0
        
        for attempt in range(max_retries):
            try:
                # Fetch pages from database
                with get_db_context() as db:
                    pages = db.query(CrawledPage).filter(
                        CrawledPage.id.in_(page_ids)
                    ).all()
                    
                    if not pages:
                        return
                    
                    # Generate embeddings (runs in thread pool, non-blocking)
                    await asyncio.get_event_loop().run_in_executor(
                        None,
                        vector_db.add_documents,
                        pages
                    )
                    
                    # Mark as processed
                    for page_id in page_ids:
                        self._processed_ids.add(page_id)
                    
                    self.processed_count += len(pages)
                    
                    app_logger.info(
                        f"✓ Embedded {len(pages)} pages "
                        f"(Total: {self.processed_count}, Queue: {self.queue.qsize()})"
                    )
                    
                    # Success - break retry loop
                    break
            
            except Exception as e:
                if attempt < max_retries - 1:
                    app_logger.warning(
                        f"Embedding batch failed (attempt {attempt + 1}/{max_retries}): {e}. "
                        f"Retrying in {retry_delay}s..."
                    )
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    self.failed_count += len(page_ids)
                    app_logger.error(
                        f"Failed to process embedding batch after {max_retries} attempts: {e}",
                        exc_info=True
                    )
    
    def get_stats(self) -> dict:
        """Get queue statistics"""
        return {
            "is_running": self.is_running,
            "queue_size": self.queue.qsize(),
            "processed_count": self.processed_count,
            "failed_count": self.failed_count,
            "unique_processed": len(self._processed_ids)
        }


# Global embedding queue instance
embedding_queue = EmbeddingQueue(batch_size=10, batch_timeout=5.0)
