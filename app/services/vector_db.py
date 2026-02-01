"""
Vector Database Service
Handles embedding generation and vector storage/retrieval
"""
import chromadb
from chromadb.config import Settings as ChromaSettings
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Optional
from pathlib import Path
import hashlib
from app.core.config import settings
from app.core.logging import app_logger
from app.models.database import CrawledPage, VectorEmbedding
from app.core.database import get_db_context


class VectorDatabase:
    """Vector database for semantic search"""
    
    def __init__(self):
        self.embedding_model = None
        self.chroma_client = None
        self.collection = None
        self._initialized = False
        # CRITICAL: Don't initialize automatically to prevent startup hangs
        app_logger.info("VectorDatabase created (lazy initialization - will load when first used)")
    
    def _initialize(self):
        """Initialize vector database and embedding model - ONLY called when actually needed"""
        if self._initialized:
            return
            
        try:
            app_logger.info("Starting lazy initialization of vector database...")
            # Initialize embedding model with device and optimization settings
            app_logger.info(f"Loading embedding model: {settings.embedding_model}")
            
            # Use CPU and optimize for low memory usage
            import torch
            device = 'cpu'
            if torch.cuda.is_available():
                app_logger.info("CUDA available but using CPU for stability")
            
            self.embedding_model = SentenceTransformer(
                settings.embedding_model,
                device=device
            )
            
            # Set to evaluation mode and optimize
            self.embedding_model.eval()
            
            app_logger.info("Embedding model loaded successfully")
            
            # Initialize ChromaDB
            db_path = Path(settings.vector_db_path)
            db_path.mkdir(parents=True, exist_ok=True)
            
            self.chroma_client = chromadb.PersistentClient(
                path=str(db_path),
                settings=ChromaSettings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # Get or create collection
            self.collection = self.chroma_client.get_or_create_collection(
                name="web_content",
                metadata={"hnsw:space": "cosine"}
            )
            
            self._initialized = True
            app_logger.info("Vector database initialized successfully")
        
        except Exception as e:
            app_logger.error(f"Error initializing vector database: {e}")
            self._initialized = False
            raise
    
    def add_documents(self, pages: List[CrawledPage]):
        """
        Add documents to vector database with batch processing
        
        Args:
            pages: List of CrawledPage objects
        """
        try:
            # app_logger.info("=== ENTER add_documents ===")
            # app_logger.info(f"Received {len(pages) if pages else 0} pages")
            
            # Ensure initialized before use
            if not self._initialized:
                app_logger.info("Initializing vector database on first use...")
                self._initialize()
            
            app_logger.info(f"Adding {len(pages)} pages to vector database...")
            
            if not pages:
                app_logger.warning("No pages to process!")
                return
            
# app_logger.info(f"Pages list type: {type(pages)}, first page type: {type(pages[0])}")
        # app_logger.info("Starting page processing loop...")
            
            total_chunks = 0
            pages_processed = 0
            
            for page_idx, page in enumerate(pages, 1):
                try:
                    # app_logger.info(f"About to process page {page_idx}: {page.url}")
                    # app_logger.info(f"Page content length: {len(page.content) if page.content else 0}")
                    
                    # Split content into chunks
                    # app_logger.info(f"Calling _split_text for page {page_idx}...")
                    chunks = self._split_text(page.content)
                # app_logger.info(f"_split_text returned {len(chunks)} chunks")
                    
                    if page_idx % 10 == 0 or page_idx == 1:
                        app_logger.info(f"Processing page {page_idx}/{len(pages)}: {page.url} ({len(chunks)} chunks)")
                except Exception as page_error:
                    app_logger.error(f"Error processing page {page_idx} ({getattr(page, 'url', 'unknown')}): {page_error}", exc_info=True)
                    continue
                
                # Process chunks in batches to control memory usage
                batch_size = settings.max_embedding_batch_size
                for batch_start in range(0, len(chunks), batch_size):
                    batch_end = min(batch_start + batch_size, len(chunks))
                    chunk_batch = chunks[batch_start:batch_end]
                    
                    # Generate embeddings for batch
                    embeddings = self.embedding_model.encode(chunk_batch, show_progress_bar=False).tolist()
                    
                    # Prepare metadata
                    metadatas = []
                    ids = []
                    
                    for i, chunk in enumerate(chunk_batch):
                        chunk_idx = batch_start + i
                        chunk_id = self._generate_chunk_id(page.url, chunk_idx)
                        
                        metadata = {
                            "url": page.url,
                            "domain": page.domain,
                            "title": page.title or "",
                            "content_type": page.content_type,
                            "chunk_index": chunk_idx,
                            "page_number": page.page_number or 0,
                            "page_id": page.id
                        }
                        
                        metadatas.append(metadata)
                        ids.append(chunk_id)
                    
                    # Add to ChromaDB in smaller batches
                    chroma_batch_size = settings.chromadb_max_batch_size
                    for cb_start in range(0, len(ids), chroma_batch_size):
                        cb_end = min(cb_start + chroma_batch_size, len(ids))
                        
                        self.collection.add(
                            embeddings=embeddings[cb_start:cb_end],
                            documents=chunk_batch[cb_start:cb_end],
                            metadatas=metadatas[cb_start:cb_end],
                            ids=ids[cb_start:cb_end]
                        )
                    
                    # Store vector IDs in database
                    with get_db_context() as db:
                        for i, chunk_id in enumerate(ids):
                            chunk_idx = batch_start + i
                            # Check if vector already exists
                            existing = db.query(VectorEmbedding).filter(
                                VectorEmbedding.vector_id == chunk_id
                            ).first()
                            
                            if not existing:
                                vector_embedding = VectorEmbedding(
                                    page_id=page.id,
                                    chunk_index=chunk_idx,
                                    chunk_text=chunk_batch[i],
                                    vector_id=chunk_id
                                )
                                db.add(vector_embedding)
                            else:
                                # Update existing embedding if content changed
                                existing.chunk_text = chunk_batch[i]
                                existing.page_id = page.id
                                existing.chunk_index = chunk_idx
                        
                        db.commit()
                
                total_chunks += len(chunks)
                pages_processed += 1
                
                if pages_processed % 10 == 0 or pages_processed == len(pages):
                    app_logger.info(f"Progress: {pages_processed}/{len(pages)} pages processed, {total_chunks} total chunks added")
            
            app_logger.info(f"Successfully added {total_chunks} total chunks from {len(pages)} pages to vector database")
            # app_logger.info("=== EXIT add_documents SUCCESS ===")
        
        except Exception as e:
            app_logger.error(f"!!! ERROR in add_documents: {e} !!!", exc_info=True)
            # app_logger.error("=== EXIT add_documents FAILURE ===")
            raise
    
    def search(
        self,
        query: str,
        top_k: Optional[int] = None,
        similarity_threshold: Optional[float] = None,
        filters: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Search vector database
        
        Args:
            query: Search query
            top_k: Number of results to return
            similarity_threshold: Minimum similarity score
            filters: Metadata filters
            
        Returns:
            List of search results with metadata
        """
        # Ensure initialized before use
        if not self._initialized:
            app_logger.info("Initializing vector database on first search...")
            self._initialize()
            
        try:
            top_k = top_k or settings.rag_top_k_results
            similarity_threshold = similarity_threshold or settings.rag_similarity_threshold
            
            app_logger.info(f"Vector search: query='{query[:50]}', top_k={top_k}, threshold={similarity_threshold}")
            
            # Generate query embedding
            query_embedding = self.embedding_model.encode([query], show_progress_bar=False).tolist()
            
            app_logger.info(f"Generated query embedding, searching collection...")
            
            # Search
            results = self.collection.query(
                query_embeddings=query_embedding,
                n_results=top_k * 2,  # Get more results to filter by threshold
                where=filters
            )
            
            app_logger.info(f"ChromaDB returned {len(results['ids'][0]) if results['ids'] and results['ids'][0] else 0} raw results")
            
            # Process results
            search_results = []
            
            if results['ids'] and results['ids'][0]:
                app_logger.info(f"Processing {len(results['ids'][0])} results, threshold={similarity_threshold}")
                for i in range(len(results['ids'][0])):
                    # Calculate similarity score (ChromaDB returns distances)
                    distance = results['distances'][0][i]
                    similarity_score = 1 - distance  # Convert distance to similarity
                    
                    if i < 3:  # Log first 3 results
                        app_logger.info(f"Result {i}: distance={distance:.4f}, similarity={similarity_score:.4f}, threshold={similarity_threshold}")
                    
                    if similarity_score >= similarity_threshold:
                        result = {
                            "id": results['ids'][0][i],
                            "text": results['documents'][0][i],
                            "metadata": results['metadatas'][0][i],
                            "similarity_score": similarity_score
                        }
                        search_results.append(result)
            else:
                app_logger.warning("No results returned from ChromaDB!")
            
            # Sort by similarity and limit to top_k
            search_results.sort(key=lambda x: x['similarity_score'], reverse=True)
            search_results = search_results[:top_k]
            
            app_logger.info(f"Returning {len(search_results)} results after filtering by threshold {similarity_threshold}")
            app_logger.debug(f"Found {len(search_results)} results for query: {query[:50]}...")
            
            return search_results
        
        except Exception as e:
            app_logger.error(f"Error searching vector database: {e}")
            return []
    
    def update_document(self, page: CrawledPage):
        """Update document in vector database"""
        try:
            # Delete existing chunks for this page
            self.delete_document(page.url)
            
            # Add updated document
            self.add_documents([page])
            
            app_logger.debug(f"Updated document in vector DB: {page.url}")
        
        except Exception as e:
            app_logger.error(f"Error updating document in vector DB: {e}")
            raise
    
    def delete_document(self, url: str):
        """Delete document from vector database"""
        try:
            # Query for all chunks from this URL
            results = self.collection.get(
                where={"url": url}
            )
            
            if results['ids']:
                self.collection.delete(ids=results['ids'])
                app_logger.debug(f"Deleted {len(results['ids'])} chunks for {url}")
            
            # Also delete from SQL database
            with get_db_context() as db:
                db.query(VectorEmbedding).filter(
                    VectorEmbedding.vector_id.in_(results['ids'])
                ).delete(synchronize_session=False)
        
        except Exception as e:
            app_logger.error(f"Error deleting document from vector DB: {e}")
            raise
    
    def get_stats(self) -> Dict:
        """Get vector database statistics"""
        # Return basic info if not initialized yet
        if not self._initialized or self.collection is None:
            return {
                "status": "not_initialized",
                "message": "Vector database will initialize on first use (lazy loading)",
                "embedding_model": settings.embedding_model,
                "total_chunks": 0
            }
        
        try:
            count = self.collection.count()
            
            return {
                "status": "initialized",
                "total_chunks": count,
                "embedding_model": settings.embedding_model,
                "collection_name": self.collection.name
            }
        
        except Exception as e:
            app_logger.error(f"Error getting vector DB stats: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def reset(self):
        """Reset vector database (delete all data)"""
        # Ensure initialized before reset
        if not self._initialized:
            app_logger.info("Initializing vector database before reset...")
            self._initialize()
            
        try:
            self.chroma_client.delete_collection("web_content")
            self.collection = self.chroma_client.create_collection(
                name="web_content",
                metadata={"hnsw:space": "cosine"}
            )
            app_logger.warning("Vector database reset")
        
        except Exception as e:
            app_logger.error(f"Error resetting vector database: {e}")
            raise
    
    def _split_text(self, text: str) -> List[str]:
        """
        Split text into chunks for embedding
        
        Args:
            text: Text to split
            
        Returns:
            List of text chunks
        """
        # app_logger.info(f"_split_text ENTER: text length={len(text) if text else 0}")
        
        chunks = []
        chunk_size = settings.chunk_size
        overlap = settings.chunk_overlap
        
        # Ensure overlap doesn't equal or exceed chunk_size to prevent infinite loop
        if overlap >= chunk_size:
            app_logger.warning(f"overlap ({overlap}) >= chunk_size ({chunk_size}), reducing overlap to chunk_size/2")
            overlap = chunk_size // 2
        
        # app_logger.info(f"_split_text: chunk_size={chunk_size}, overlap={overlap}")
        
        # Simple character-based chunking
        # In production, consider using more sophisticated methods
        # like sentence-based or semantic chunking
        
        start = 0
        text_length = len(text)
        
        # app_logger.info(f"_split_text: Starting loop, text_length={text_length}")
        
        iteration = 0
        while start < text_length:
            iteration += 1
            # if iteration % 10 == 0:
            #     app_logger.info(f"_split_text: iteration {iteration}, start={start}/{text_length}")
            
            # Safety check to prevent infinite loops
            if iteration > 10000:
                app_logger.error(f"_split_text: Breaking infinite loop at iteration {iteration}, start={start}")
                break
            
            end = start + chunk_size
            
            # Try to break at sentence boundary (but only if it doesn't make chunk too small)
            if end < text_length:
                # Look for sentence endings
                for punct in ['. ', '! ', '? ', '\n\n']:
                    last_punct = text.rfind(punct, start + chunk_size // 2, end)  # Only search in second half
                    if last_punct != -1:
                        end = last_punct + len(punct)
                        break
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            # Ensure we always advance, never go backwards
            new_start = max(start + 1, end - overlap)  # At minimum, advance by 1 char
            start = new_start
        
        # app_logger.info(f"_split_text EXIT: returning {len(chunks)} chunks after {iteration} iterations")
        return chunks
    
    def _generate_chunk_id(self, url: str, chunk_index: int) -> str:
        """Generate unique ID for chunk"""
        content = f"{url}_{chunk_index}"
        return hashlib.md5(content.encode()).hexdigest()


# Global vector database instance
vector_db = VectorDatabase()
