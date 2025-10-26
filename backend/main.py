import asyncio
import logging
import os
from pathlib import Path
from typing import List
from fastapi import FastAPI, UploadFile, File, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import json

from services.graphrag_service import GraphRAGService
from services.chat_service import ChatService
from models import Case, CaseCreate

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

UPLOAD_DIR = Path("./uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

graphrag_service = GraphRAGService()
chat_service = ChatService()


@app.on_event("startup")
async def startup():
    await graphrag_service.initialize()


@app.on_event("shutdown")
async def shutdown():
    await graphrag_service.close()


@app.post("/cases", response_model=Case)
async def create_case(case: CaseCreate):
    """Create a new case."""
    case_dir = UPLOAD_DIR / case.name
    case_dir.mkdir(exist_ok=True)
    return Case(id=case.name, name=case.name, document_count=0)


@app.get("/cases", response_model=List[Case])
async def list_cases():
    """List all cases."""
    cases = []
    for case_dir in UPLOAD_DIR.iterdir():
        if case_dir.is_dir():
            doc_count = len(list(case_dir.glob("*")))
            cases.append(Case(id=case_dir.name, name=case_dir.name, document_count=doc_count))
    return cases


@app.post("/cases/{case_id}/upload")
async def upload_documents(case_id: str, files: List[UploadFile] = File(...)):
    """Upload documents to a case."""
    case_dir = UPLOAD_DIR / case_id
    if not case_dir.exists():
        raise HTTPException(status_code=404, detail="Case not found")
    
    uploaded_files = []
    for file in files:
        file_path = case_dir / file.filename
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        await graphrag_service.process_document(str(file_path), case_id)
        uploaded_files.append(file.filename)
    
    return {"uploaded": uploaded_files, "count": len(uploaded_files)}


@app.get("/cases/{case_id}/graph")
async def get_case_graph(case_id: str):
    """Get graph data for visualization."""
    return await graphrag_service.get_graph_data(case_id)


@app.websocket("/ws/chat/{case_id}")
async def chat_websocket(websocket: WebSocket, case_id: str):
    """WebSocket endpoint for chat."""
    await websocket.accept()
    
    try:
        while True:
            message = await websocket.receive_text()
            
            async for chunk in chat_service.chat_stream(message, case_id, graphrag_service):
                await websocket.send_text(json.dumps({"type": "chunk", "content": chunk}))
            
            await websocket.send_text(json.dumps({"type": "done"}))
    
    except WebSocketDisconnect:
        logger.info(f"Client disconnected from case {case_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
