import logging
import os
from pathlib import Path
from typing import List
from fastapi import FastAPI, UploadFile, File, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import json

from services.graphrag_service import GraphRAGService
from services.chat_service import ChatService
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Legal Document GraphRAG")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = Path("./uploads/documents")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

graphrag_service = GraphRAGService()
chat_service = ChatService()


@app.on_event("startup")
async def startup():
    await graphrag_service.initialize()


@app.on_event("shutdown")
async def shutdown():
    await graphrag_service.close()


@app.get("/documents")
async def list_documents():
    """List all uploaded documents."""
    documents = []
    for file_path in UPLOAD_DIR.glob("*"):
        if file_path.is_file():
            documents.append({
                "name": file_path.name,
                "size": file_path.stat().st_size
            })
    return {"documents": documents, "count": len(documents)}


@app.post("/upload")
async def upload_documents(files: List[UploadFile] = File(...)):
    """Upload documents."""
    uploaded_files = []
    for file in files:
        file_path = UPLOAD_DIR / file.filename
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        await graphrag_service.process_document(str(file_path))
        uploaded_files.append(file.filename)
    
    return {"uploaded": uploaded_files, "count": len(uploaded_files)}


@app.get("/graph")
async def get_graph():
    """Get graph data for visualization."""
    return await graphrag_service.get_graph_data()


@app.websocket("/ws/chat")
async def chat_websocket(websocket: WebSocket):
    """WebSocket endpoint for chat."""
    await websocket.accept()
    
    try:
        while True:
            message = await websocket.receive_text()
            
            async for chunk in chat_service.chat_stream(message, graphrag_service):
                await websocket.send_text(json.dumps({"type": "chunk", "content": chunk}))
            
            await websocket.send_text(json.dumps({"type": "done"}))
    
    except WebSocketDisconnect:
        logger.info("Client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
