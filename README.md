# Audio Search

Search your recordings by meaning, then jump to the exact moment.
Example query: "that call about payment retries".

**Flow:** upload audio -> faster-whisper transcribes with timestamps -> 30s chunks -> embeddings -> Chroma -> query returns start time -> player seeks.

**Stack:** FastAPI, faster-whisper, sentence-transformers, ChromaDB, React (Vite), Docker. All free and local.

## Run locally
```bash
# backend
cd backend && python -m venv venv && source venv/bin/activate
pip install -r requirements.txt && uvicorn main:app --reload

# frontend (new terminal)
cd frontend && npm install && npm run dev
```
Open http://localhost:5173

## Run with Docker
```bash
docker compose up --build
```

## Ideas for next
Speaker diarization, hybrid search (BM25 + vectors), auth, S3 storage.
