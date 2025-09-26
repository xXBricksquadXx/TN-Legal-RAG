# TN-Legal-RAG

Local, private RAG demo for Tennessee regulations using **FastAPI + ChromaDB + Ollama**.  
Upload `.txt`/`.md` files, ask questions, and get grounded answers from your own corpus.

> Runs fully offline once your Ollama model is pulled. No cloud keys required.

---

## 🔧 Stack

- **FastAPI** – lightweight API + minimal web UI  
- **ChromaDB** – local vector store on disk (`.chroma/`)  
- **Sentence Transformers** – text embeddings (defaults to `all-MiniLM-L6-v2`)  
- **Ollama** – local LLM inference (defaults to `qwen2.5:1.5b-instruct`)  

---

## ✅ Prerequisites

- Linux/WSL (Ubuntu 22.04+ recommended)
- Python 3.12+
- Ollama installed and running (`systemctl status ollama`)
- Git (if developing)

---

## ▶️ Quickstart

```bash
# 1) clone and enter
git clone git@github.com:xXBricksquadXx/TN-Legal-RAG.git
cd TN-Legal-RAG

# 2) python venv
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip

# 3) install deps
pip install -r requirements.txt  # if present
# or explicitly:
pip install chromadb sentence-transformers fastapi uvicorn aiofiles python-multipart requests

# 4) pull a small local model (first pull can take a bit)
# tip: qwen2.5 1.5B is fast & decent; tinyllama is even smaller
ollama pull qwen2.5:1.5b-instruct

# 5) create docs folder (if missing)
mkdir -p docs

# 6) optional: seed a test doc
echo "Barb’s Place is open Wed–Sun, 4pm–2am." > docs/barbs_hours.txt

# 7) build the index (creates ./.chroma)
python indexer.py

# 8) run the API + UI
uvicorn rag_api:app --reload --host 127.0.0.1 --port 8000

# Open `http://127.0.0.1:8000` for a `minimal UI`:
Ask questions in the top box
Upload `.txt/.md` files
Delete docs by path (e.g., `docs/foo.md`)
```
---

## 📦 Project Structure

```bash

TN-Legal-RAG/
├─ rag_api.py           # FastAPI app + minimal HTML UI
├─ indexer.py           # one-shot index builder for ./docs
├─ docs/                # place your source files here (.txt/.md)
├─ .chroma/             # ChromaDB persistent store (created at runtime)
├─ .gitignore
└─ README.md

```

---
## 🔌 API Endpoints
`GET` / – simple HTML UI

`POST /upload` – multipart file upload (`file`)

`POST /query` – JSON `{ "q": "question", "k": 3, "max_tokens": 256 }`

`POST /delete` – JSON `{ "id": "docs/filename.md" }`

Example query via curl:

```bash
curl -X POST "http://127.0.0.1:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"q":"When was rule 0020-01-.08 most recently amended?","k":3}'
```

---

## ⚙️ Configuration
Default model + ports are hardcoded for simplicity. You can override via env vars:

`OLLAMA_HOST` (default `http://127.0.0.1:11434`)
`OLLAMA_MODEL` (default `qwen2.5:1.5b-instruct`)
`EMBED_MODEL` (default `sentence-transformers/all-MiniLM-L6-v2`)
Export before running `uvicorn`, for example:
```bash
export OLLAMA_MODEL="tinyllama"
export EMBED_MODEL="sentence-transformers/all-MiniLM-L12-v2"
```

---

## 🧪 Good queries to try
List all amendment dates you can find for Chapter 0020-01.”

“When was rule 0020-01-.08 most recently amended?”

“Summarize the changes mentioned for 0020-02-.02 in 2016 and 2024.”

Tip: Add your own curated .md notes per rule to improve retrieval quality.
---

## 🛠 Troubleshooting
Ollama 404: `curl 127.0.0.1:11434/api/tags` → if empty/unreachable:
`sudo systemctl start ollama && sudo systemctl enable ollama`

Model missing: `ollama pull qwen2.5:1.5b-instruct`

Chroma legacy error: You’re on new Chroma API. This repo already uses the
new client style; if you migrated data from an old setup, rebuild the index:
`rm -rf .chroma && python indexer.py`

Port busy: Something else is on 8000 — change with --port 8080.

Slow / OOM: Use a tiny Ollama model, and keep `k` small (e.g., `k=3`).
---

## 🔒 Privacy & Security
Everything stays on your machine.

Do not commit `.chroma/`, `.venv/`, or raw proprietary docs.

If you deploy on a server, put it behind a reverse proxy + TLS and require auth.
---

🗺 Roadmap (TN-focused)
Scraper / importer for TN regs + rule history → normalized .md files

Chunking + metadata (rule id, chapter, dates) to improve retrieval

Citation rendering with source snippets in the UI

Evaluation set (Q/A pairs) for automatic quality tracking

Auth + audit log (basic JWT) for multi-user deployments

Packaging for systemd (run as a service), optional HTTPS via Caddy/NGINX

---

## 🤝 Contributing

PRs welcome! Keep changes small and documented. Please open issues for bugs or feature ideas.





