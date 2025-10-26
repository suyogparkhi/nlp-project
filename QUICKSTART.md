# Quick Start Guide

## 1. Install Neo4j

Download and install Neo4j Desktop from https://neo4j.com/download/

Create a new database with:

- Password: `admin123` (or update in `.env`)
- Start the database

## 2. Get API Keys

### Google Gemini API Key

1. Go to https://makersuite.google.com/app/apikey
2. Create an API key
3. Save it for the `.env` file

### OpenAI API Key

1. Go to https://platform.openai.com/api-keys
2. Create an API key
3. Save it for the `.env` file

### Google Cloud Credentials (for Vertex AI)

1. Go to https://console.cloud.google.com/
2. Create a service account with Vertex AI permissions
3. Download the JSON credentials file
4. Save the path for the `.env` file

## 3. Setup Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env

# Edit .env with your credentials:
# NEO4J_URI=neo4j://localhost:7687
# NEO4J_USER=neo4j
# NEO4J_PASSWORD=admin123
# OPENAI_API_KEY=sk-...
# GEMINI_API_KEY=AI...
# GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json

# Run the server
python main.py
```

Backend will run on http://localhost:8000

## 4. Setup Frontend

```bash
cd frontend

# Install dependencies
npm install

# Run dev server
npm run dev
```

Frontend will run on http://localhost:5173

## 5. Use the Application

1. Open http://localhost:5173 in your browser
2. Create a new case (e.g., "Smith vs Jones")
3. Click on the case to open it
4. Upload documents (PDF, DOC, DOCX, TXT)
5. Wait for processing (check backend logs)
6. View the Knowledge Graph tab to see relationships
7. Use the Chat tab to ask questions about your documents

## Troubleshooting

### Neo4j Connection Error

- Ensure Neo4j is running
- Check the URI and credentials in `.env`
- Default is `neo4j://localhost:7687`

### Document Processing Fails

- Check backend logs for errors
- Ensure all API keys are valid
- Verify Google Cloud credentials are correct

### Graph Not Showing

- Upload documents first
- Wait for processing to complete
- Check browser console for errors

### Chat Not Working

- Ensure WebSocket connection is established
- Check GEMINI_API_KEY is valid
- Verify documents have been processed
