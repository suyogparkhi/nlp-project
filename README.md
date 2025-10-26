# Legal Document GraphRAG Assistant

A document management system for lawyers with GraphRAG capabilities, allowing bulk document upload, knowledge graph visualization, and AI-powered chat.

## Features

- **Case Management**: Organize documents by legal cases
- **Bulk Upload**: Upload multiple documents (PDF, DOC, DOCX, TXT)
- **Knowledge Graph**: Visualize document relationships using Neo4j GraphRAG
- **AI Chat**: Ask questions about documents using Gemini
- **Local Storage**: All files stored locally

## Prerequisites

1. **Neo4j Database**: Install and run Neo4j locally

   - Download from https://neo4j.com/download/
   - Default connection: `neo4j://localhost:7687`
   - Set password to `admin123` or update `.env`

2. **Python 3.9+**: For backend

3. **Node.js 18+**: For frontend

4. **API Keys**:
   - Google Cloud credentials for Vertex AI (Gemini)
   - OpenAI API key for embeddings

## Setup

### Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env with your credentials

# Run server
python main.py
```

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Run dev server
npm run dev
```

## Usage

1. Start Neo4j database
2. Start backend server (port 8000)
3. Start frontend dev server (port 5173)
4. Open http://localhost:5173
5. Create a case
6. Upload documents
7. View knowledge graph
8. Chat with your documents

## Architecture

- **Backend**: FastAPI with WebSocket for real-time chat
- **GraphRAG**: Neo4j with SimpleKGPipeline for document processing
- **LLM**: Google Gemini 2.0 Flash for chat
- **Frontend**: React + TypeScript with react-force-graph for visualization
- **Storage**: Local filesystem for documents

## API Endpoints

- `POST /cases` - Create new case
- `GET /cases` - List all cases
- `POST /cases/{case_id}/upload` - Upload documents
- `GET /cases/{case_id}/graph` - Get graph data
- `WS /ws/chat/{case_id}` - WebSocket chat endpoint
