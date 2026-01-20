# TN-Legal-RAG

<img width="1536" height="1024" alt="TN-Legal-RAG Hero" src="https://github.com/user-attachments/assets/f378d568-c1ee-4a50-879c-487105163652" />

### **Precision Retrieval for Tennessee Statutes & Regulations**

**TN-Legal-RAG** is a mission-focused, private RAG (Retrieval-Augmented Generation) system designed for legal professionals and researchers. It provides grounded, citeable answers from a localized corpus including the Tennessee Code Annotated (TCA), Administrative Rules, and specialized Evidence distinctions.

---

## 📌 Living Change Log

### Latest verified run (2026-01-20)

* **Corpus**: `70 files` indexed (`python3 indexer.py`)
* **Verification workflow**: `./scripts/check_all.sh`

  * Rebuilt index and reloaded persistent `.chroma`
  * API health check: **OK**
  * Smoke test: **OK**
  * API eval: **8/8 passed** (FAST, workers=8)

#### Snapshot outputs (sanity checks)

* **Eligibility**

  * Output: `"TN citizens have access to public records through the TPRA."`
  * Sources:

    * `docs/tn/code/tca-10-7-505-denial-of-access-remedy.md`
    * `docs/tn/code/tca-10-7-503-public-records-act.md`
    * `docs/tn/sunshine/oorc-best-practices-and-guidelines-2022-09-19.md`

* **TDOS**

  * Output: `"Use the TDOS Open Records contact on this page — email Safety.OpenRecords@tn.gov or the listed Nashville addresses; fees follow OORC."`
  * Sources:

    * `docs/tn/sunshine/tdos-open-records.md`

* **Fees**

  * Output:

    * `### Copy Charges:`
    * `- B/W: $0.15/page`
    * `- Color: $0.50/page`
    * `### Labor Charge:`
    * `- May be charged after the first hour of staff time (retrieval, review, redaction) using the lowest-paid qualified employee; with itemized time.`
    * `**Note:** Refer to OORC Schedule of Reasonable Charges for additional details.`
  * Sources:

    * `docs/tn/sunshine/oorc-schedule-of-reasonable-charges.md`

---

## 🛡 Performance & Verification

**Evaluation Suite: 100% Pass Rate** The system is hardened against the 404/retrieval errors common in lightweight RAG setups. Current benchmarks verify zero-hallucination retrieval for core statutory questions.

| Case ID                        | Objective                             | Status | Mode |
| :----------------------------- | :------------------------------------ | :----- | :--- |
| **tca-records-act**            | Public Records Custodian              | ✅ PASS | Fast |
| **bar-404b-distinction**       | Clear & Convincing Standard           | ✅ PASS | Fast |
| **confidentiality-exceptions** | TBI/Medical Record Exceptions         | ✅ PASS | Fast |
| **budget-fy25**                | Fiscal Year 2025 Totals               | ✅ PASS | Fast |
| **minority-representation**    | Representation / qualification checks | ✅ PASS | Fast |
| **county-quorum**              | County quorum / rules validation      | ✅ PASS | Fast |
| **mayor-veto-budget**          | Mayor veto budget constraints         | ✅ PASS | Fast |
| **budget-deadline-dept**       | Department budget deadline checks     | ✅ PASS | Fast |

---

## 🛠 Tech Stack

* **Engine**: FastAPI (Backend) + Ollama (Local Inference)
* **Vector Store**: ChromaDB (Disk-persistent)
* **Intelligence**: Qwen 2.5 (1.5B Instruct) — Balanced for local GPU efficiency.
* **Embeddings**: `all-MiniLM-L6-v2` (Sentence Transformers)
* **Interface**: Modern Apple-style Glassmorphism UI with integrated source citations.

---

## 🚀 Deployment & Workflow

### 1. Initialize Environment

```bash
# Clone and enter
git clone git@github.com:xXBricksquadXx/TN-Legal-RAG.git
cd TN-Legal-RAG

# Create and activate venv
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

---

## 2. Index the Corpus

Drop your .md, .txt, or normalized legal documents into the `docs/` folder. The indexer handles paragraph-aware chunking and metadata extraction.

```bash
python3 indexer.py
```

---

## 3. Launch Interface

Start the hardened API and Browser UI

```bash
uvicorn rag_api:app --reload
```

Access the dashboard at `http://127.0.0.1:8000`

---

<img width="1919" height="886" alt="image" src="https://github.com/user-attachments/assets/69f5b13e-8fd7-44d2-9346-9ec0dc9e5607" />

---

## 🔌 API Endpoints

* `GET /`: Glassmorphic User Interface.
* `GET /health`: API status check (used by `check_all.sh`).
* `POST /query`: Full RAG generation (LLM-powered).
* `POST /debug_query`: Fast retrieval check (Context-only, no LLM cost).

---

## 🔒 Professional Standards & Privacy

* `100% Local`: No legal data or queries leave your machine. Fully compatible with air-gapped workstations.
* `High-Fidelity Sources`: The system is tuned to prioritize statutory text (TCA) over secondary interpretations.
* `Deterministic Evaluation`: Includes a custom testing framework (`/scripts`) to ensure consistency before committing new data.

---

## 🗺 Roadmap

[ ] `Unified Normalizer`: Scripting to conform Justia, Lexis, and Supreme Court formatting into a single schema.

[ ] `Supreme Court Opinion Integration`: Specialized chunking for long-form judicial opinions.

[ ] `Hybrid Search`: Combining semantic vectors with BM25 keyword search for specific T.C.A. citations.

[ ] `Priority Metadata`: Ranking statutes higher than guides in the retrieval chain.

---

## ☕ Support / Follow

If you find this useful:

* `Watch / Star` the repo to keep up with weekly TN updates.
* `Share the project` with researchers who need local, offline legal RAG.
