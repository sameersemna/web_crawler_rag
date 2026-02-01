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
        self._initialize()
    
    def _initialize(self):
        """Initialize vector database and embedding model"""
        try:
            # Initialize embedding model
            app_logger.info(f"Loading embedding model: {settings.embedding_model}")
            self.embedding_model = SentenceTransformer(settings.embedding_model)
            
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
            
            app_logger.info("Vector database initialized successfully")
        
        except Exception as e:
            app_logger.error(f"Error initializing vector database: {e}")
            raise
    
    def add_documents(self, pages: List[CrawledPage]):
        """
        Add documents to vector database
        
        Args:
            pages: List of CrawledPage objects
        """
        try:
            for page in pages:
                # Split content into chunks
                chunks = self._split_text(page.content)
                
                # Generate embeddings
                embeddings = self.embedding_model.encode(chunks).tolist()
                
                # Prepare metadata
                metadatas = []
                ids = []
                
                for i, chunk in enumerate(chunks):
                    chunk_id = self._generate_chunk_id(page.url, i)
                    
                    metadata = {
                        "url": page.url,
                        "domain": page.domain,
                        "title": page.title or "",
                        "content_type": page.content_type,
                        "chunk_index": i,
                        "page_number": page.page_number or 0,
                        "page_id": page.id
                    }
                    
                    metadatas.append(metadata)
                    ids.append(chunk_id)
                
                # Add to ChromaDB
                self.collection.add(
                    embeddings=embeddings,
                    documents=chunks,
                    metadatas=metadatas,
                    ids=ids
                )
                
                # Store vector IDs in database
                with get_db_context() as db:
                    for i, chunk_id in enumerate(ids):
                        # Check if vector already exists
                        existing = db.query(VectorEmbedding).filter(
                            VectorEmbedding.vector_id == chunk_id
                        ).first()
                        
                        if not existing:
                            vector_embedding = VectorEmbedding(
                                page_id=page.id,
                                chunk_index=i,
                                chunk_text=chunks[i],
                                vector_id=chunk_id
                            )
                            db.add(vector_embedding)
                        else:
                            # Update existing embedding if content changed
                            existing.chunk_text = chunks[i]
                            existing.page_id = page.id
                            existing.chunk_index = i
                
                app_logger.debug(f"Added {len(chunks)} chunks from {page.url} to vector DB")
        
        except Exception as e:
            app_logger.error(f"Error adding documents to vector DB: {e}")
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
        try:
            top_k = top_k or settings.rag_top_k_results
            similarity_threshold = similarity_threshold or settings.rag_similarity_threshold
            
            # Generate query embedding
            query_embedding = self.embedding_model.encode([query]).tolist()
            
            # Search
            results = self.collection.query(
                query_embeddings=query_embedding,
                n_results=top_k * 2,  # Get more results to filter by threshold
                where=filters
            )
            
            # Process results
            search_results = []
            
            if results['ids'] and results['ids'][0]:
                for i in range(len(results['ids'][0])):
                    # Calculate similarity score (ChromaDB returns distances)
                    distance = results['distances'][0][i]
                    similarity_score = 1 - distance  # Convert distance to similarity
                    
                    if similarity_score >= similarity_threshold:
                        result = {
                            "id": results['ids'][0][i],
                            "text": results['documents'][0][i],
                            "metadata": results['metadatas'][0][i],
                            "similarity_score": similarity_score
                        }
                        search_results.append(result)
            
            # Sort by similarity and limit to top_k
            search_results.sort(key=lambda x: x['similarity_score'], reverse=True)
            search_results = search_results[:top_k]
            
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
        try:
            count = self.collection.count()
            
            return {
                "total_chunks": count,
                "embedding_model": settings.embedding_model,
                "collection_name": self.collection.name
            }
        
        except Exception as e:
            app_logger.error(f"Error getting vector DB stats: {e}")
            return {}
    
    def reset(self):
        """Reset vector database (delete all data)"""
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
        chunks = []
        chunk_size = settings.chunk_size
        overlap = settings.chunk_overlap
        
        # Simple character-based chunking
        # In production, consider using more sophisticated methods
        # like sentence-based or semantic chunking
        
        start = 0
        text_length = len(text)
        
        while start < text_length:
            end = start + chunk_size
            
            # Try to break at sentence boundary
            if end < text_length:
                # Look for sentence endings
                for punct in ['. ', '! ', '? ', '\n\n']:
                    last_punct = text.rfind(punct, start, end)
                    if last_punct != -1:
                        end = last_punct + len(punct)
                        break
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = end - overlap
        
        return chunks
    
    def _generate_chunk_id(self, url: str, chunk_index: int) -> str:
        """Generate unique ID for chunk"""
        content = f"{url}_{chunk_index}"
        return hashlib.md5(content.encode()).hexdigest()


# Global vector database instance
vector_db = VectorDatabase()
