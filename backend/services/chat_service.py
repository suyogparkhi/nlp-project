import os
import logging
from typing import AsyncGenerator
import asyncio

logger = logging.getLogger(__name__)


class ChatService:
    async def chat_stream(
        self, 
        message: str, 
        case_id: str, 
        graphrag_service
    ) -> AsyncGenerator[str, None]:
        """Stream chat responses using GraphRAG with VectorRetriever."""
        try:
            # Run the synchronous GraphRAG search in a thread pool
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: graphrag_service.query_graph(message, case_id)
            )
            
            # GraphRAG returns a response object with .answer attribute
            if hasattr(response, 'answer'):
                answer = response.answer
            elif isinstance(response, dict) and 'answer' in response:
                answer = response['answer']
            else:
                answer = str(response)
            
            # Stream the response in chunks for better UX
            chunk_size = 50
            for i in range(0, len(answer), chunk_size):
                yield answer[i:i + chunk_size]
        
        except Exception as e:
            logger.error(f"Chat error: {e}")
            yield f"Error: {str(e)}"
