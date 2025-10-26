import os
import logging
from typing import AsyncGenerator
import google.generativeai as genai

logger = logging.getLogger(__name__)


class ChatService:
    def __init__(self):
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        if not gemini_api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        genai.configure(api_key=gemini_api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash')
    
    async def chat_stream(
        self, 
        message: str, 
        case_id: str, 
        graphrag_service
    ) -> AsyncGenerator[str, None]:
        """Stream chat responses using Gemini."""
        try:
            context = await graphrag_service.search_context(message, case_id)
            
            prompt = f"""You are a legal assistant helping lawyers analyze documents.
            
Context from documents:
{context}

User question: {message}

Provide a clear, professional answer based on the context. If the context doesn't contain relevant information, say so."""
            
            response = await self.model.generate_content_async(
                prompt,
                stream=True
            )
            
            async for chunk in response:
                if chunk.text:
                    yield chunk.text
        
        except Exception as e:
            logger.error(f"Chat error: {e}")
            yield f"Error: {str(e)}"
