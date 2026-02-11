# TN-Legal-RAG

<img width="1536" height="1024" alt="TN-Legal-RAG Hero" src="https://github.com/user-attachments/assets/f378d568-c1ee-4a50-879c-487105163652" />

### Precision Retrieval for Tennessee Statutes & Regulations

**TN-Legal-RAG** is a mission-focused, private RAG (Retrieval-Augmented Generation) system designed for legal professionals and researchers. It provides grounded, citeable answers from a localized corpus including the Tennessee Code Annotated (TCA), Administrative Rules, and specialized Evidence distinctions.

---

## Living Change Log

### Latest verified run (2026-02-11)

* **Corpus:** `84 files` indexed via **Modular Chunking** (`python3 indexer.py`)
* **Architecture upgrade:** moved from simple Bi-Encoder retrieval to a **Hybrid Re-Ranking Pipeline** (Bi-Encoder + Cross-Encoder)
* **Verification workflow:** `./scripts/check_all.sh`

  * Rebuilt index: **Verified (Header-Aware)**
  * API health check: **OK** (extended wait time for dual-model loading)
  * Smoke test: **OK** (hallucination check: TPRA confirmed TN-specific; no Texas/TPIA leakage)
  * API eval: **16/16 passed** (LLM mode, workers=8) — **100% success rate**

#### Snapshot outputs (sanity checks)

* **Eligibility**

  * Output: `"Any Tennessee citizen is entitled to inspect state, county, and municipal records under the Tennessee Public Records Act (TPRA)."`
  * Sources: `docs/tn/code/tca-10-7-503-public-records-act.md`, `docs/tn/sunshine/public-records-act-quickref-2025.md`

* **Right to Farm (New Case Law)**

  * Output: `"Established poultry farms are protected under the Right to Farm Act from nuisance suits by residents who move in after the farm has been operating for at least one year."`
  * Sources: `docs/tn/opinions/sc/estate_of_johnson_v_smith.md`

* **Fees**

  * Output:

    * `B/W: $0.15/page`
    * `Color: $0.50/page`
    * `Labor: Chargeable after the first hour of staff time.`
  * Sources: `docs/tn/sunshine/oorc-schedule-of-reasonable-charges.md`

---
<div align="center">
  <h3>🎥 Proof of Life: Supreme Court Retrieval</h3>
  <video src="https://github.com/user-attachments/assets/55401a79-0445-4328-a99a-7843bbba1c15" width="100%" controls></video>
</div>

---

## Performance & Verification

**Evaluation Suite: 16/16 Pass Rate**
The system is hardened against cross-jurisdictional hallucinations and "context smearing" through modular indexing and precision re-ranking.

| Case ID                        | Objective                          | Status | Mode |
| ------------------------------ | ---------------------------------- | ------ | ---- |
| **tca-records-act**            | Public Records Custodian           | ✅ PASS | Fast |
| **confidentiality-exceptions** | TBI/Medical Record Exceptions      | ✅ PASS | Fast |
| **county-quorum**              | 5-5-108 "Majority" Rule            | ✅ PASS | Fast |
| **budget-deadline-dept**       | March 1st Budget Submission        | ✅ PASS | Fast |
| **ag-labor-workers-comp**      | Landscaping Exemption (Martinez)   | ✅ PASS | Fast |
| **drone-privacy-curtilage**    | Warrantless Surveillance (Miller)  | ✅ PASS | Fast |
| **right-to-farm-nuisance**     | Residential Encroachment (Johnson) | ✅ PASS | Fast |
| **arbitration-jurisdiction**   | SC Case Law (Berkeley Opinion)     | ✅ PASS | Fast |

---

## Tech Stack (The "Kicker" Architecture)

* **Engine:** FastAPI (backend) + Ollama (local inference)
* **Vector store:** ChromaDB (disk-persistent)
* **Intelligence:** Qwen 2.5 (1.5B Instruct) — temperature `0.0` for legal determinism
* **Retrieval pipeline:**

  1. **Modular indexing:** header-aware splitting (`##`, `###`) prevents statutory context blending
  2. **Wide-net retrieval:** semantic search pulls top `25–60` candidates using `all-MiniLM-L6-v2`
  3. **Precision re-ranking:** `cross-encoder/ms-marco-MiniLM-L-6-v2` re-scores candidates to find logical matches (e.g., specific TCA subsections) that simple vectors might miss
* **Interface:** modern Apple-style glassmorphism UI with integrated source citations

---

## Deployment & Workflow

### 1) Initialize environment & Ollama

Ensure you have Ollama installed and the model pulled:

```bash
ollama pull qwen2.5:1.5b-instruct
ollama serve
```

Clone and set up the Python env:

```bash
# Clone and enter
git clone git@github.com:xXBricksquadXx/TN-Legal-RAG.git
cd TN-Legal-RAG

# Create and activate venv
python3 -m venv .venv
source .venv/bin/activate

# Install deps
pip install -r requirements.txt
```

### 2) Index the corpus (Modular)

Drop your `.md`, `.txt`, or normalized legal documents into `docs/`.
The indexer handles **Header-Aware** chunking to keep sub-modules intact.

```bash
python3 indexer.py
```

### 3) Launch interface

Start the hardened API and browser UI:

```bash
uvicorn rag_api:app --reload
```

Access the dashboard at `http://127.0.0.1:8000`

### 4) Verify integrity (The "Check All" script)

Run the full suite (Rebuild Index → Health Check → Smoke Test → Evals):

```bash
./scripts/check_all.sh
```

<img width="1161" height="543" alt="Screenshot 2026-02-03 094452" src="https://github.com/user-attachments/assets/08ac8bdf-43b9-44a0-b171-7a472dc42c8f" />

---

## API Endpoints

* `GET /` — glassmorphic user interface
* `GET /health` — API status check (wait logic included for model loading)
* `POST /query` — full RAG generation (LLM-powered)
* `POST /debug_query` — fast retrieval check; returns raw documents and sources after re-ranking

---

## Professional Standards & Privacy

* **100% local:** no legal data or queries leave your machine
* **High-fidelity sources:** prioritizes statutory text (TCA) over secondary interpretations
* **Hallucination defense:** includes a custom testing framework (`/scripts`) to verify TN-specific logic; every file includes a human-proofed Practitioner Summary to anchor the LLM

---

## Roadmap

* [x] County Governance ingest: comprehensive Title 5 coverage
* [x] Supreme Court opinion integration: support for 2025–2026 opinions (Martinez, Johnson, Miller)
* [x] Precision re-ranking: integrated Cross-Encoder for accuracy
* [ ] Unified normalizer: scripting to conform Justia/Lexis formatting into a single schema
* [ ] Containerization: Docker support for "ship-anywhere" deployment

---

## Support / Follow

If you find this useful:

* Watch / Star the repo to keep up with weekly TN updates
* Share the project with researchers who need local, offline legal RAG
