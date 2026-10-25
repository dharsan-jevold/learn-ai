<div align="center">
  <img src="./banner.png" alt="Smart AI Study Assistant" width="100%" />
</div>

# Smart AI Study Assistant — Local Setup

A study assistant for adding notes, uploading study documents, and asking questions about their contents. The current local configuration runs language generation and semantic embeddings through [Ollama](https://ollama.com/) on your computer.

## Current setup

- **Frontend:** React 19, Vite, Tailwind CSS
- **Backend:** FastAPI and Python
- **Local language model:** `llama3:latest` through Ollama
- **Local embedding model:** `nomic-embed-text:latest` through Ollama
- **Authentication:** Supabase Auth
- **Notes and history:** local JSON fallback at `backend/data/notes.json` until the Supabase tables and vector-search function are configured

No OpenRouter or Jina API key is required for the current Smart AI workflow. Ollama runs the models locally. Supabase Auth still requires an internet connection and a Supabase project.

## How it works

1. Sign in through Supabase Auth.
2. Add a note or upload a document. The backend extracts its text and splits it into chunks.
3. Ollama's `nomic-embed-text` converts each chunk into an embedding vector.
4. When you ask a Smart AI question, the same embedding model converts the question. The backend finds relevant note chunks using vector similarity.
5. Ollama's `llama3` receives the question and retrieved study text, then generates the answer.

Classic mode uses keyword matching. Smart AI mode uses semantic search and a local language model. Answers show the note or document used as a source when one is found.

## Requirements

- Windows 10 or later, macOS, or Linux
- Python 3.10 or later
- Node.js 18 or later
- [Ollama](https://ollama.com/download)
- A Supabase project for account sign-in

The Ollama models used by this setup are:

```text
llama3:latest
nomic-embed-text:latest
```

Download them once if they are not already installed:

```powershell
ollama pull llama3
ollama pull nomic-embed-text
ollama list
```

Keep the Ollama app or service running while using Smart AI. The first response may take longer while Ollama loads the model into memory.

## Configure the backend

From the project folder, create and activate a Python virtual environment, then install the dependencies:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Create `backend/.env` with your Supabase project URL and legacy anon key:

```env
SUPABASE_URL=https://YOUR_PROJECT.supabase.co
SUPABASE_ANON_KEY=YOUR_SUPABASE_ANON_KEY
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_CHAT_MODEL=llama3:latest
OLLAMA_EMBED_MODEL=nomic-embed-text:latest
```

The Ollama values are optional because the backend uses these defaults. Do not put a Supabase service-role key or any private API key in the frontend. `.env` files are ignored by Git; use real credentials only in your local environment.

Start the backend from the `backend` folder:

```powershell
python -m uvicorn main:app --reload --port 8000
```

The API documentation is available at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

## Configure and start the frontend

In a second terminal, from the project folder:

```powershell
cd frontend
npm install
```

Create `frontend/.env`:

```env
VITE_API_URL=http://127.0.0.1:8000/api
```

Start Vite:

```powershell
npm run dev
```

Open the local address printed by Vite, usually [http://localhost:5173](http://localhost:5173).

## Try the app

1. Sign up or log in. Supabase email confirmation may need to be completed before the first login.
2. Add a note or upload a text-based document.
3. Open Ask AI, choose Smart AI, and ask a question that the note or document answers.
4. Check that the response cites the relevant source.

PDFs and office documents need extractable text. Scanned or image-only files are not OCR'd by the current upload path. Llama 3 is text-only here, so image questions are not supported.

## Where data is stored

Supabase Auth handles login. The current Supabase database does not yet have this app's `study_notes` and `ask_history` tables or `match_study_notes` RPC function. Until those are set up, the backend falls back to `backend/data/notes.json` for notes, embeddings, and history. Local data stays on this computer and does not sync to other devices.

The local JSON fallback is suitable for development and a personal local run. For cloud note storage, configure the Supabase schema and permissions to match `backend/database.py` before relying on the database. The schema notes from the original cloud-oriented version may need updating for the current code.

## Troubleshooting

- **Ollama connection error:** Make sure the Ollama app/service is running and the backend can reach `http://127.0.0.1:11434`.
- **Model not found:** Run `ollama list` and confirm both model names above are present.
- **No relevant notes:** Upload or add the material again after changing embedding models so it receives embeddings from `nomic-embed-text`.
- **Supabase table or RPC errors:** The app currently falls back to local JSON when those database objects are missing. Login still requires valid Supabase settings.
- **Document extraction error:** Try a plain `.txt` or a document with selectable text. Image-only scans are not OCR'd.

## Local-only note

This configuration expects Ollama at `127.0.0.1` on the same computer as the backend. A separately hosted backend cannot reach the Ollama service on your laptop through that address. The local configuration is intended for development and personal use.
