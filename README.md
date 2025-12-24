<img width="1536" height="1024" alt="TN-Legal-RAG" src="https://github.com/user-attachments/assets/f378d568-c1ee-4a50-879c-487105163652" />

---
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
## ✅ API + UI
```bash
(.venv) colby@______:~/TN-Legal-RAG$ uvicorn rag_api:app --reload --host 127.0.0.1 --port 8000
INFO:     Will watch for changes in these directories: ['/home/colby/TN-Legal-RAG']
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [26957] using WatchFiles
INFO:     Started server process [26959]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     127.0.0.1:47974 - "GET / HTTP/1.1" 200 OK
INFO:     127.0.0.1:47974 - "GET /favicon.ico HTTP/1.1" 404 Not Found
INFO:     127.0.0.1:58510 - "GET /health HTTP/1.1" 200 OK
INFO:     127.0.0.1:58514 - "POST /query HTTP/1.1" 200 OK
INFO:     127.0.0.1:37994 - "POST /query HTTP/1.1" 200 OK
INFO:     127.0.0.1:53906 - "POST /query HTTP/1.1" 200 OK
INFO:     127.0.0.1:40844 - "POST /query HTTP/1.1" 200 OK
INFO:     127.0.0.1:40752 - "POST /query HTTP/1.1" 200 OK
INFO:     127.0.0.1:52688 - "POST /query HTTP/1.1" 200 OK
INFO:     127.0.0.1:33276 - "POST /query HTTP/1.1" 200 OK
INFO:     127.0.0.1:58036 - "POST /query HTTP/1.1" 200 OK
INFO:     127.0.0.1:35106 - "POST /query HTTP/1.1" 200 OK
INFO:     127.0.0.1:38028 - "POST /query HTTP/1.1" 200 OK
INFO:     127.0.0.1:41410 - "POST /query HTTP/1.1" 200 OK
INFO:     127.0.0.1:56274 - "POST /query HTTP/1.1" 200 OK
INFO:     127.0.0.1:47034 - "POST /query HTTP/1.1" 200 OK
INFO:     127.0.0.1:47050 - "POST /query HTTP/1.1" 200 OK
INFO:     127.0.0.1:47996 - "POST /query HTTP/1.1" 200 OK
INFO:     127.0.0.1:50936 - "POST /query HTTP/1.1" 200 OK
INFO:     127.0.0.1:47414 - "POST /query HTTP/1.1" 200 OK
INFO:     127.0.0.1:39394 - "POST /query HTTP/1.1" 200 OK
INFO:     127.0.0.1:38992 - "POST /query HTTP/1.1" 200 OK
INFO:     127.0.0.1:45758 - "POST /query HTTP/1.1" 200 OK
INFO:     127.0.0.1:51228 - "POST /query HTTP/1.1" 200 OK
```
---

## 💨 Smoke Test

```bash
(.venv) colby@_________:~/TN-Legal-RAG$ cd ~/TN-Legal-RAG
./scripts/check_all.sh
>>> Rebuilding index
Indexed 143 chunks from 48 files → ./.chroma

>>> Smoke test
Health:
{
  "ok": true,
  "collection": "tn_legal",
  "model": "qwen2.5:1.5b-instruct",
  "embed": "all-MiniLM-L6-v2",
  "max_distance": 0.75
}
Eligibility:
"TN citizens."
[
  "docs/tn/code/tca-10-7-503-public-records-act.md",
  "docs/tn/sunshine/oorc-best-practices-and-guidelines-2022-09-19.md",
  "docs/tn/code/tca-10-7-507-traffic-conviction-records.md",
  "docs/tn/code/tca-10-7-505-denial-of-access-remedy.md",
  "docs/tn/sunshine/tdos-open-records.md"
]
TDOS:
"Use the TDOS Open Records contact on this page — email **Safety.OpenRecords@tn.gov** or the listed Nashville addresses; fees follow OORC."
[
  "docs/tn/sunshine/tdos-open-records.md",
  "docs/tn/sunshine/oorc-best-practices-and-guidelines-2022-09-19.md"
]
Fees:
"Copy charges are up to $0.15/page (B/W) and $0.50/page (color). Labor may be charged after the first hour of staff time, using the lowest-paid qualified employee, with time itemized."
[
  "docs/tn/sunshine/oorc-schedule-of-reasonable-charges.md"
]

>>> API eval

Results: 47/47 passed

✅ tpra-eligibility: text=True src=True
✅ tdos-portal: text=True src=True
✅ tdos-fees: text=True src=True
✅ oorc-fee-schedule: text=True src=True
✅ oorc-labor-threshold: text=True src=True
✅ oorc-best-practices-response-time: text=True src=True
✅ tpra-core-definition-public-record: text=True src=True
✅ tpra-inspection-vs-copies: text=True src=True
✅ tpra-seven-business-days-rule: text=True src=True
✅ tpra-residency-proof: text=True src=True
✅ tpra-redaction-vs-withholding: text=True src=True
✅ tpra-injunction-intent-to-disrupt: text=True src=True
✅ tca-1-1-101-members: text=True src=True
✅ tca-1-1-102-chair-secretary: text=True src=True
✅ tca-1-1-103-staff-services: text=True src=True
✅ tca-1-1-104-successor: text=True src=True
✅ tca-1-1-105-publication: text=True src=True
✅ tca-1-1-106-contracts: text=True src=True
✅ tca-1-1-107-specs-price: text=True src=True
✅ tca-1-1-108-substantive-changes: text=True src=True
✅ tca-10-7-101-records-construed: text=True src=True
✅ tca-10-7-102-register-books: text=True src=True
✅ tca-10-7-104-mutilated-records: text=True src=True
✅ tca-10-7-105-rebinding-copying: text=True src=True
✅ tca-10-7-106-transcript-certification: text=True src=True
✅ tca-10-7-107-omission-of-probate: text=True src=True
✅ tca-10-7-108-entering-omitted-probate: text=True src=True
✅ tca-10-7-109-clerk-probate-copy: text=True src=True
✅ tca-10-7-110-entry-in-transcript-book: text=True src=True
✅ tca-10-7-112-index-transcript-books: text=True src=True
✅ tca-10-7-113-special-deputies: text=True src=True
✅ tca-10-7-114-register-fees: text=True src=True
✅ tca-10-7-115-original-deposited-clerk: text=True src=True
✅ tca-10-7-116-copy-from-original-evidence: text=True src=True
✅ tca-10-7-118-copies-transcribed-records: text=True src=True
✅ tca-10-7-119-rebinding-authority: text=True src=True
✅ tca-10-7-120-liability-suspended-rebinding: text=True src=True
✅ tca-10-7-121-computer-records: text=True src=True
✅ tca-10-7-123-electronic-access: text=True src=True
✅ tca-10-7-501-microfilm-authority: text=True src=True
✅ tca-10-7-502-photographic-copy-original: text=True src=True
✅ tca-10-7-505-remedies: text=True src=True
✅ tca-10-7-506-commercial-gis-fees: text=True src=True
✅ tca-10-7-507-traffic-conviction-records: text=True src=True
✅ tca-10-7-508-archival-review: text=True src=True
✅ tca-10-7-509-state-records-disposition: text=True src=True
✅ tca-10-7-510-historical-transfer: text=True src=True
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
"List all amendment dates you can find for Chapter 0020-01.”

“When was rule 0020-01-.08 most recently amended?”

“Summarize the changes mentioned for 0020-02-.02 in 2016 and 2024.”

<img width="1919" height="1195" alt="TN-Legal-Rag" src="https://github.com/user-attachments/assets/8b145fbd-830e-418f-a99a-3c8d2367e675" />

>Tip: Add your own curated .md notes per rule to improve retrieval quality.
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





