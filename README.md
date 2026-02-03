# TN-Legal-RAG

<img width="1536" height="1024" alt="TN-Legal-RAG Hero" src="https://github.com/user-attachments/assets/f378d568-c1ee-4a50-879c-487105163652" />

### **Precision Retrieval for Tennessee Statutes & Regulations**

**TN-Legal-RAG** is a mission-focused, private RAG (Retrieval-Augmented Generation) system designed for legal professionals and researchers. It provides grounded, citeable answers from a localized corpus including the Tennessee Code Annotated (TCA), Administrative Rules, and specialized Evidence distinctions.

---

## 📌 Living Change Log

### Latest verified run (2026-02-03)

* **Corpus**: `80 files` indexed (`python3 indexer.py`) — **+10 from previous baseline.**
* **Verification workflow**: `./scripts/check_all.sh`
  * Rebuilt index and reloaded persistent `.chroma`: **Verified**
  * API health check: **OK**
  * Smoke test: **OK** (Hallucination check: TPRA residency confirmed as TN-specific)
  * API eval: **13/13 passed** (FAST mode, workers=8) — **100% Success Rate.**

#### Snapshot outputs (sanity checks)

* **Eligibility**
  * Output: `"TN citizens have access to public records through the TPRA."`
  * Sources:
    * `docs/tn/code/tca-10-7-505-denial-of-access-remedy.md`
    * `docs/tn/code/tca-10-7-503-public-records-act.md`
    * `docs/tn/sunshine/oorc-best-practices-and-guidelines-2022-09-19.md`

* **County Governance**
  * Output: `"The county mayor serves as a nonvoting ex officio member of the legislative body and its committees."`
  * Sources:
    * `docs/tn/code/tca-5-6-106-mayor-duties.md`

* **Fees**
  * Output: 
    * `### Copy Charges:`
    * `- B/W: $0.15/page`
    * `- Color: $0.50/page`
    * `### Labor Charge:`
    * `- May be charged after the first hour of staff time using the lowest-paid qualified employee.`
  * Sources:
    * `docs/tn/sunshine/oorc-schedule-of-reasonable-charges.md`

---

## 🛡 Performance & Verification

**Evaluation Suite: 100% Pass Rate**
The system is hardened against cross-jurisdictional hallucinations (e.g., swapping TN for TX) through expert practitioner summaries and deterministic evaluation.

| Case ID | Objective | Status | Mode |
| :--- | :--- | :--- | :--- |
| **tca-records-act** | Public Records Custodian | ✅ PASS | Fast |
| **arbitration-jurisdiction**| SC Case Law (Berkeley Opinion) | ✅ PASS | Fast |
| **county-vacancies** | 7-day Public Notice Rules | ✅ PASS | Fast |
| **mayor-ex-officio** | Mayor's voting limits | ✅ PASS | Fast |
| **redistricting-timeline** | 10-year reapportionment cycle | ✅ PASS | Fast |
| **finance-centralization** | Hospital exclusion rules (2/3 vote) | ✅ PASS | Fast |
| **confidentiality-exceptions**| TBI/Medical Record Exceptions | ✅ PASS | Fast |
| **budget-fy25** | Fiscal Year 2025 Totals | ✅ PASS | Fast |

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

### 2. Index the Corpus

Drop your .md, .txt, or normalized legal documents into the `docs/ folder`. The indexer handles paragraph-aware chunking and metadata extraction.
```bash
python3 indexer.py
```
### 3. Launch Interface

Start the hardened API and Browser UI
```bash
uvicorn rag_api:app --reload
```
Access the dashboard at `http://127.0.0.1:8000`
---
<img width="1161" height="543" alt="Screenshot 2026-02-03 094452" src="https://github.com/user-attachments/assets/08ac8bdf-43b9-44a0-b171-7a472dc42c8f" />

### 🔌 API Endpoints
  - GET /: Glassmorphic User Interface.
  - GET /health: API status check (used by check_all.sh).
  - POST /query: Full RAG generation (LLM-powered).
  - POST /debug_query: Fast retrieval check (Context-only, no LLM cost).

### 🔒 Professional Standards & Privacy
  - 100% Local: No legal data or queries leave your machine.
  - High-Fidelity Sources: Prioritizes statutory text (TCA) over secondary interpretations.
  - Hallucination Defense: Includes a custom testing framework (/scripts) to verify TN-specific logic before committing new data. Every file includes a human-proofed Practitioner Summary to anchor the LLM.

### 🗺 Roadmap

[x] County Governance Ingest: Comprehensive Title 5 coverage. 

[x] Supreme Court Opinion Integration: Initial support for 2025-2026 opinions. 

[ ] Unified Normalizer: Scripting to conform Justia/Lexis formatting into a single schema. 

[ ] Hybrid Search: Combining semantic vectors with BM25 keyword search for TCA citations.

### ☕ Support / Follow

 If you find this useful:
  - Watch / Star the repo to keep up with weekly TN updates.
  - Share the project with researchers who need local, offline legal RAG.


