# TN-Legal-RAG

<img width="1536" height="1024" alt="TN-Legal-RAG Hero" src="https://github.com/user-attachments/assets/f378d568-c1ee-4a50-879c-487105163652" />

### Precision Retrieval for Tennessee Statutes & Regulations

**TN-Legal-RAG** is a mission-focused, private RAG (Retrieval-Augmented Generation) system designed for legal professionals and researchers. It provides grounded, citeable answers from a localized corpus including the Tennessee Code Annotated (TCA), Administrative Rules, and specialized Appellate/Supreme Court case law.

---

## Living Change Log

### Latest verified run (2026-04-10)

* **Corpus:** `98 files` indexed via **Modular Chunking** (`python3 indexer.py`) — *Added Open Meetings Act (TOMA) & TPRA Willful Denial Case Law.*
* **Architecture upgrade:** WSL-to-Windows GPU Bridging established. Hybrid Re-Ranking Pipeline (Bi-Encoder + Cross-Encoder).
* **Ingestion automation:** Deployed `auto_ingest.py` (LLM-powered unified normalizer for Justia/Lexis scraping).
* **Verification workflow:** `./scripts/check_all.sh`
  * Rebuilt index: **Verified (Header-Aware)**
  * API health check: **OK** (120-attempt window for heavy Cross-Encoder loading)
  * Smoke test: **OK** (TOMA & TPRA hallucination checks passed)
  * API eval: **23/23 passed** (FAST mode, workers=8) — **100% success rate**

#### Snapshot outputs (sanity checks)

* **Open Meetings (TOMA) & Secret Ballots**
  * Output: `"No, a county commission cannot hold a closed executive session or use secret ballots. The Tennessee Open Meetings Act (TOMA) prohibits exceptions for closed meetings, and all votes must be vocal and public."`
  * Sources: `docs/tn/code/tca-8-44-104-minutes-recorded.md`, `docs/tn/opinions/sc/dorrier_v_dark.md`

* **Willful Denial (TPRA)**
  * Output: `"If a county requires you to appear in person to request a public record, it constitutes a willful violation of the TPRA and justifies an award of attorney's fees."`
  * Sources: `docs/tn/opinions/coa/friedmann_v_marshall_county.md`

* **Right to Farm (New Case Law)**
  * Output: `"Established poultry farms are protected under the Right to Farm Act from nuisance suits by residents who move in after the farm has been operating for at least one year."`
  * Sources: `docs/tn/opinions/sc/estate_of_johnson_v_smith.md`

---
<div align="center">
  <h3>🎥 Proof of Life: Supreme Court Retrieval</h3>
  <video src="https://github.com/user-attachments/assets/3e82288b-b061-4a93-a7bb-5d977fc4fe37" width="100%" controls></video>
</div>

---

## Performance & Verification

**Evaluation Suite: 23/23 Pass Rate**
The system is hardened against cross-jurisdictional hallucinations and "context smearing" through modular indexing and precision re-ranking.

| Case ID                        | Objective                                  | Status | Mode |
| ------------------------------ | ------------------------------------------ | ------ | ---- |
| **tca-records-act** | Public Records Custodian                   | ✅ PASS | Fast |
| **tpra-attorney-fees** | Willful Denial & Fee Recovery (10-7-505)   | ✅ PASS | Fast |
| **tpra-commercial-value-news** | GIS Data Fees & Media Exemption (10-7-506) | ✅ PASS | Fast |
| **toma-secret-ballots** | T.C.A. 8-44-104 Voting Requirements        | ✅ PASS | Fast |
| **toma-action-nullified** | T.C.A. 8-44-105 Illegal Meeting Sanctions  | ✅ PASS | Fast |
| **toma-enforcement-jurisdiction**| Chancery/Circuit Court Authority         | ✅ PASS | Fast |
| **county-quorum** | 5-5-108 "Majority" Rule                    | ✅ PASS | Fast |
| **right-to-farm-nuisance** | Residential Encroachment (Johnson)         | ✅ PASS | Fast |
| **arbitration-jurisdiction** | SC Case Law (Berkeley Opinion)             | ✅ PASS | Fast |
| **ag-labor-workers-comp** | Landscaping Exemption (Martinez)           | ✅ PASS | Fast |

---

## Tech Stack (The "Kicker" Architecture)

* **Engine:** FastAPI (backend) + Ollama (local Windows host inference)
* **Vector store:** ChromaDB (disk-persistent)
* **Intelligence:** Qwen 2.5 (1.5B Instruct) — temperature `0.0` for legal determinism
* **Retrieval pipeline:**
  1. **Modular indexing:** header-aware splitting (`##`, `###`) prevents statutory context blending
  2. **Wide-net retrieval:** semantic search pulls top `40–60` candidates using `all-MiniLM-L6-v2`
  3. **Precision re-ranking:** `cross-encoder/ms-marco-MiniLM-L-6-v2` re-scores candidates to find logical matches that simple vectors might miss
* **Interface:** modern Apple-style glassmorphism UI with integrated source citations

---

## Deployment & Workflow

### 1) Initialize Windows Ollama & WSL Environment

To maximize GPU performance, Ollama runs natively on the Windows Host while the Python API runs in WSL Ubuntu.

**On Windows Host (PowerShell Admin):**
Ensure Ollama listens to the WSL virtual network and allow it through the firewall:
```powershell
$env:OLLAMA_HOST="0.0.0.0"
New-NetFirewallRule -DisplayName "Ollama WSL Bridge" -Direction Inbound -Action Allow -Protocol TCP -LocalPort 11434 -Profile Any
ollama run qwen2.5:1.5b-instruct
```

### On WSL Ubuntu:
Extract your true Windows Gateway IP and update `OLLAMA_URL` in `rag_api.py`:

```bash
WIN_IP=$(ip route show default | awk '{print $3}')
echo "Update rag_api.py with this IP: $WIN_IP"
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

### 2) Ingest & Index the Corpus (Modular)

**Step A: Auto-Ingest Raw Text**
Drop raw, unformatted text from Justia or Lexis into `docs/raw_imports/` as `.txt` files. Run the automated LLM normalizer to generate perfect Markdown with Practitioner Summaries:
```bash
python3 tools/auto_ingest.py
```

### 3) Index the corpus (Modular)

Move the reviewed `.md` files from `docs/staging/` to their final homes in `docs/tn/code/` or `docs/tn/opinions/`.

```bash
python3 indexer.py
```

### 4) Launch interface

Start the hardened API and browser UI:

```bash
uvicorn rag_api:app --reload
```

Access the dashboard at `http://127.0.0.1:8000`

### 5) Verify integrity (The "Check All" script)

Run the full suite (Rebuild Index → Health Check → Smoke Test → Evals):

```bash
./scripts/check_all.sh
```

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

* [x] **County Governance Ingest**: Comprehensive Title 5 coverage
* [x] **Sunshine Law Ingest**: TOMA and TPRA willful denial case law
* [x] **Precision Re-ranking**: Integrated Cross-Encoder for accuracy
* [x] **Unified normalizer**: Deployed `auto_ingest.py` to conform Justia/Lexis text via local LLM parsing
* [ ] **Containerization**: Docker support for "ship-anywhere" deployment

---

## Support / Follow

If you find this useful:

* Watch / Star the repo to keep up with weekly TN updates
* Share the project with researchers who need local, offline legal RAG
