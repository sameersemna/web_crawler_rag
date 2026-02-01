"""
LLM Service
Handles interaction with Gemini and DeepSeek APIs
"""
from typing import List, Dict, Optional
import google.generativeai as genai
from openai import OpenAI
from app.core.config import settings
from app.core.logging import app_logger


class LLMService:
    """Service for interacting with LLM APIs"""
    
    def __init__(self):
        self.gemini_client = None
        self.deepseek_client = None
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize LLM clients"""
        try:
            # Initialize Gemini
            if settings.gemini_api_key:
                genai.configure(api_key=settings.gemini_api_key)
                self.gemini_client = genai.GenerativeModel('gemini-pro')
                app_logger.info("Gemini client initialized")
            
            # Initialize DeepSeek (uses OpenAI-compatible API)
            if settings.deepseek_api_key:
                self.deepseek_client = OpenAI(
                    api_key=settings.deepseek_api_key,
                    base_url="https://api.deepseek.com"
                )
                app_logger.info("DeepSeek client initialized")
        
        except Exception as e:
            app_logger.error(f"Error initializing LLM clients: {e}")
    
    async def generate_response(
        self,
        query: str,
        context: List[Dict],
        provider: Optional[str] = None,
        additional_context: Optional[str] = None,
        temperature: Optional[float] = None
    ) -> Dict:
        """
        Generate response using LLM
        
        Args:
            query: User query
            context: List of context chunks from vector search
            provider: LLM provider (gemini or deepseek)
            additional_context: Additional context from user
            temperature: Temperature for generation
            
        Returns:
            Dictionary with response and metadata
        """
        provider = provider or settings.default_llm_provider
        temperature = temperature or settings.llm_temperature
        
        try:
            # Build prompt
            prompt = self._build_prompt(query, context, additional_context)
            
            # Generate response based on provider
            if provider == "gemini":
                response = await self._generate_gemini(prompt, temperature)
            elif provider == "deepseek":
                response = await self._generate_deepseek(prompt, temperature)
            else:
                raise ValueError(f"Unsupported LLM provider: {provider}")
            
            return {
                "answer": response,
                "provider": provider,
                "success": True
            }
        
        except Exception as e:
            app_logger.error(f"Error generating LLM response: {e}")
            return {
                "answer": f"Error generating response: {str(e)}",
                "provider": provider,
                "success": False,
                "error": str(e)
            }
    
    async def _generate_gemini(self, prompt: str, temperature: float) -> str:
        """Generate response using Gemini"""
        if not self.gemini_client:
            raise ValueError("Gemini client not initialized. Check API key.")
        
        try:
            generation_config = genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=settings.llm_max_tokens,
                top_p=settings.llm_top_p
            )
            
            response = self.gemini_client.generate_content(
                prompt,
                generation_config=generation_config
            )
            
            return response.text
        
        except Exception as e:
            app_logger.error(f"Gemini API error: {e}")
            raise
    
    async def _generate_deepseek(self, prompt: str, temperature: float) -> str:
        """Generate response using DeepSeek"""
        if not self.deepseek_client:
            raise ValueError("DeepSeek client not initialized. Check API key.")
        
        try:
            response = self.deepseek_client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that answers questions based on provided context."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=temperature,
                max_tokens=settings.llm_max_tokens,
                top_p=settings.llm_top_p
            )
            
            return response.choices[0].message.content
        
        except Exception as e:
            app_logger.error(f"DeepSeek API error: {e}")
            raise
    
    def _build_prompt(
        self,
        query: str,
        context: List[Dict],
        additional_context: Optional[str] = None
    ) -> str:
        """
        Build prompt for LLM
        
        Args:
            query: User query
            context: List of context chunks
            additional_context: Additional context from user
            
        Returns:
            Formatted prompt
        """
        # Build context section
        context_parts = []
        for i, ctx in enumerate(context, 1):
            source_info = f"Source {i}: {ctx['metadata']['url']}"
            if ctx['metadata'].get('page_number', 0) > 0:
                source_info += f" (Page {ctx['metadata']['page_number']})"
            
            context_parts.append(
                f"{source_info}\n"
                f"{ctx['text']}\n"
            )
        
        context_text = "\n---\n".join(context_parts)
        
        # Build full prompt
        prompt = f"""You are a helpful assistant that answers questions based on the provided context from crawled websites.

Context from websites:
{context_text}

"""
        
        if additional_context:
            prompt += f"""Additional Context:
{additional_context}

"""
        
        prompt += f"""Question: {query}

Instructions:
1. Answer the question based ONLY on the information provided in the context above
2. If the context doesn't contain enough information to answer the question, say so
3. Be specific and cite which source(s) you're using in your answer
4. Provide a clear, concise, and accurate answer
5. If information comes from a PDF, mention the page number when relevant

Answer:"""
        
        return prompt
    
    def check_provider_availability(self, provider: str) -> bool:
        """Check if LLM provider is available"""
        if provider == "gemini":
            return self.gemini_client is not None
        elif provider == "deepseek":
            return self.deepseek_client is not None
        return False
    
    def get_available_providers(self) -> List[str]:
        """Get list of available LLM providers"""
        providers = []
        if self.gemini_client:
            providers.append("gemini")
        if self.deepseek_client:
            providers.append("deepseek")
        return providers


# Global LLM service instance
llm_service = LLMService()
