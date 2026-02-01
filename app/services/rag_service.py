"""
RAG (Retrieval-Augmented Generation) Service
Combines vector search with LLM for question answering
"""
from typing import List, Optional
from datetime import datetime
import time
from app.services.vector_db import vector_db
from app.services.llm_service import llm_service
from app.models.schemas import RAGQueryRequest, RAGQueryResponse, SourceReference
from app.core.config import settings
from app.core.logging import app_logger


class RAGService:
    """Service for RAG-based question answering"""
    
    def __init__(self):
        self.vector_db = vector_db
        self.llm_service = llm_service
    
    async def query(self, request: RAGQueryRequest) -> RAGQueryResponse:
        """
        Process RAG query
        
        Args:
            request: RAG query request
            
        Returns:
            RAG query response with answer and sources
        """
        start_time = time.time()
        
        try:
            # Determine parameters
            top_k = request.top_k or settings.rag_top_k_results
            snippet_length = request.snippet_length or settings.snippet_length
            provider = request.llm_provider or settings.default_llm_provider
            temperature = request.temperature or settings.llm_temperature
            
            # Search vector database
            app_logger.info(f"Processing query: {request.query[:50]}...")
            search_results = self.vector_db.search(
                query=request.query,
                top_k=top_k
            )
            
            if not search_results:
                return RAGQueryResponse(
                    query=request.query,
                    answer="I couldn't find any relevant information in the crawled websites to answer your question.",
                    sources=[],
                    llm_provider=provider,
                    processing_time_ms=(time.time() - start_time) * 1000,
                    confidence_score=0.0
                )
            
            # Generate answer using LLM
            llm_response = await self.llm_service.generate_response(
                query=request.query,
                context=search_results,
                provider=provider,
                additional_context=request.context,
                temperature=temperature
            )
            
            # Build source references
            sources = []
            if request.include_sources:
                sources = self._build_source_references(
                    search_results=search_results,
                    snippet_length=snippet_length
                )
            
            # Calculate average confidence score
            avg_similarity = sum(r['similarity_score'] for r in search_results) / len(search_results)
            
            processing_time_ms = (time.time() - start_time) * 1000
            
            response = RAGQueryResponse(
                query=request.query,
                answer=llm_response['answer'],
                sources=sources,
                llm_provider=provider,
                confidence_score=avg_similarity,
                processing_time_ms=processing_time_ms
            )
            
            app_logger.info(
                f"Query processed in {processing_time_ms:.2f}ms, "
                f"found {len(sources)} sources"
            )
            
            return response
        
        except Exception as e:
            app_logger.error(f"Error processing RAG query: {e}")
            raise
    
    def _build_source_references(
        self,
        search_results: List[dict],
        snippet_length: int
    ) -> List[SourceReference]:
        """
        Build source references from search results
        
        Args:
            search_results: Search results from vector database
            snippet_length: Maximum length of snippet
            
        Returns:
            List of source references
        """
        sources = []
        
        for result in search_results:
            metadata = result['metadata']
            text = result['text']
            
            # Create snippet
            snippet = self._create_snippet(text, snippet_length)
            
            # Find highlighted text (most relevant part)
            highlighted_text = self._extract_highlight(text, snippet_length)
            
            source = SourceReference(
                url=metadata['url'],
                domain=metadata['domain'],
                title=metadata.get('title'),
                snippet=snippet,
                similarity_score=result['similarity_score'],
                page_number=metadata.get('page_number') if metadata.get('page_number', 0) > 0 else None,
                highlighted_text=highlighted_text,
                content_type=metadata['content_type']
            )
            
            sources.append(source)
        
        return sources
    
    def _create_snippet(self, text: str, max_length: int) -> str:
        """
        Create snippet from text
        
        Args:
            text: Full text
            max_length: Maximum snippet length
            
        Returns:
            Text snippet
        """
        if len(text) <= max_length:
            return text
        
        # Try to break at sentence boundary
        snippet = text[:max_length]
        last_period = snippet.rfind('. ')
        
        if last_period > max_length * 0.5:  # At least 50% of max_length
            snippet = snippet[:last_period + 1]
        
        return snippet + "..."
    
    def _extract_highlight(self, text: str, max_length: int) -> str:
        """
        Extract most relevant highlight from text
        
        Args:
            text: Full text
            max_length: Maximum highlight length
            
        Returns:
            Highlighted text
        """
        # For now, return beginning of text
        # In production, could use more sophisticated methods to find
        # the most relevant sentence based on query keywords
        
        sentences = text.split('. ')
        highlight = sentences[0] if sentences else text[:max_length]
        
        if len(highlight) > max_length:
            highlight = highlight[:max_length] + "..."
        
        return highlight
    
    async def get_similar_queries(self, query: str, top_k: int = 5) -> List[str]:
        """
        Get similar queries (for autocomplete/suggestions)
        
        Args:
            query: Query text
            top_k: Number of similar queries to return
            
        Returns:
            List of similar query texts
        """
        # This could be implemented by maintaining a query history
        # and finding similar queries using embeddings
        # For now, return empty list
        return []


# Global RAG service instance
rag_service = RAGService()
