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
### Clone the repository

```bash
git clone https://github.com/suyogparkhi/nlp-project.git
cd nlp-project
```

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

---

## Environment variables

If `.env.example` is not present, create a `.env` file in `backend/` with the following keys:

```env
NEO4J_URI=neo4j://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=admin123
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=AI...
GOOGLE_APPLICATION_CREDENTIALS=/absolute/path/to/google-credentials.json
NEO4J_INDEX_NAME=chunk-embeddings
```

See `QUICKSTART.md` for a more guided setup.

## Datasets, models, and preprocessing

- **Dataset**: This app operates on user-provided legal documents. No fixed public dataset is bundled. For testing, sample PDFs exist under `backend/uploads/test/`.
- **Preprocessing**:
  - PDFs and text files are chunked and parsed by `neo4j-graphrag`’s `SimpleKGPipeline`.
  - Chunks are embedded with OpenAI `text-embedding-3-large` (dimension 3072) and written into Neo4j.
  - A knowledge graph is generated (entities/relations) and nodes tagged with `document_path`.
- **Models/Services**:
  - Embeddings: OpenAI `text-embedding-3-large` (requires `OPENAI_API_KEY`).
  - LLM: Vertex AI Gemini (configured via Google Cloud credentials).
  - Vector index: Created in Neo4j on the embedding property (default name `chunk-embeddings`).

No model files are downloaded locally; cloud APIs are used. Ensure API keys/credentials are set before running.

## Repository structure

```text
nlp-project/
  backend/
    main.py                  # FastAPI app (upload, graph, WebSocket chat)
    models.py
    requirements.txt
    services/
      chat_service.py        # Streaming chat using GraphRAG
      graphrag_service.py    # Neo4j + embeddings + KG pipeline + retriever
    uploads/
      test/                  # Sample documents for local testing
    upgrade_deps.sh
  frontend/
    package.json
    src/
      api.ts                 # API wrappers
      components/            # Chat, FileUpload, GraphView
      App.tsx, main.tsx, ... # React app
  QUICKSTART.md              # Step-by-step setup and troubleshooting
  README.md                  # This file
```

## Examples

### Example input
- Upload a PDF such as `backend/uploads/test/Modify Itinerary.pdf` via the UI (Frontend → Upload), or with API:
  ```bash
  curl -F "files=@backend/uploads/test/Modify Itinerary.pdf" http://localhost:8000/upload
  ```

### Example output (graph data)
`GET http://localhost:8000/graph` returns a lightweight graph snapshot for visualization:

```json
{
  "nodes": [
    { "id": "node-1", "label": "Booking", "type": "__Chunk__" }
    // ...
  ],
  "edges": [
    { "source": "node-1", "target": "node-2", "label": "REFERS_TO" }
    // ...
  ]
}
```

### Example chat
Connect from the frontend or a WebSocket client to `ws://localhost:8000/ws/chat` and send:
```
What is the refund policy mentioned in the itinerary?
```
You will receive a streamed textual answer grounded on the retrieved chunks/graph context.

## Diagram

```mermaid
flowchart LR
  A[React + Vite (Frontend)] -- REST/WS --> B[FastAPI Backend]
  B -- Neo4j driver --> C[(Neo4j)]
  B -- Embeddings --> D[OpenAI API]
  B -- LLM (chat + KG) --> E[Vertex AI Gemini]
  subgraph Local
    A
    B
    C
  end
```

## Technologies used

- **Languages**: Python, TypeScript
- **Backend**: FastAPI, WebSockets, python-dotenv
- **GraphRAG / Graph**: neo4j, neo4j-graphrag
- **LLM**: google-cloud-aiplatform, google-generativeai (Vertex AI Gemini)
- **Embeddings**: openai (text-embedding-3-large)
- **Frontend**: React, Vite, TypeScript
- **Infra/Tools**: Neo4j Desktop/Server, Node.js, npm

## Run locally (TL;DR)

```bash
# 1) Neo4j
# Install and run Neo4j locally, set password to admin123 (or update .env)

# 2) Backend
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
# Create backend/.env (see Environment variables section)
python main.py

# 3) Frontend
cd ../frontend
npm install
npm run dev

# Open the app
# http://localhost:5173
```
