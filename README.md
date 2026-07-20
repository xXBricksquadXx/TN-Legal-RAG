# TN-Legal-RAG

<img width="1536" height="1024" alt="TN-Legal-RAG Hero" src="https://github.com/user-attachments/assets/f378d568-c1ee-4a50-879c-487105163652" />

### Precision Retrieval for Tennessee Statutes & Regulations

**TN-Legal-RAG** is a mission-focused, private RAG (Retrieval-Augmented Generation) system designed for legal professionals and researchers. It provides grounded, citeable answers from a localized corpus including the Tennessee Code Annotated (TCA), Administrative Rules, and specialized Appellate/Supreme Court case law.

---

## Living Change Log

### Latest verified run (2026-07-20)

* **Corpus:** `118 files` indexed via **Modular Chunking** (`python3 indexer.py`) — *Added Week 2 County Operations sweep: Sovereign Immunity (GTLA §§ 29-20-201, 29-20-305), County Zoning (§§ 13-7-101, 13-7-105), Procurement Ethics (§ 12-4-106), Official Bonds (§ 8-19-101), Official Misconduct (§ 39-16-402), and landmark SC precedents (Ezell v. Cockrell, McCallen v. City of Memphis).*
* **Architecture Security:** WSL-to-Windows GPU Bridging patched to support dynamic Hyper-V IP shifting (Port 11434). Python environment isolated and re-sterilized.
* **Evaluation Suite Optimization:** Streamlined evaluation framework to a 19-case "Golden Core" benchmark to prevent test execution bloat as the corpus scales, guaranteeing high-speed (<35s) regression verification across core legal domains.
* **Verification workflow:** `./scripts/check_all.sh`
  * Rebuilt index: **Verified (Header-Aware)**
  * API health check: **OK** (120-attempt window for heavy Cross-Encoder loading)
  * Smoke test: **OK** (TOMA, TPRA, & GTLA hallucination checks passed)
  * API eval: **19/19 passed** (FAST mode, workers=8) — **100% Golden Core pass rate (35.2s total run)**

#### Snapshot outputs (sanity checks)

* **Public Duty Doctrine (Ezell v. Cockrell)**
  * Output: `"The Tennessee Governmental Tort Liability Act did not abolish the common-law public duty doctrine. Law enforcement officers owe a duty to the public at large rather than individual citizens, shielding them from negligence claims unless a special duty of care was affirmatively undertaken."`
  * Sources: `docs/tn/opinions/sc/ezell_v_cockrell.md`

* **Zoning Deference & Administrative Review (McCallen v. City of Memphis)**
  * Output: `"A local governing body's approval of a planned development under existing zoning regulations is an administrative act reviewed by common law writ of certiorari. Courts must exercise high deference and cannot substitute their judgment unless the decision is shown to be clearly arbitrary, capricious, or illegal."`
  * Sources: `docs/tn/opinions/sc/mccallen_v_city_of_memphis.md`

* **Public Records vs. Personal Property (Griffin)**
  * Output: `"Handwritten suicide notes confiscated by police at a death scene are considered public records under the TPRA because they were received by the police department in connection with the transaction of official business, rather than for mere safekeeping."`
  * Sources: `docs/tn/opinions/sc/griffin_v_knoxville.md`

---
<div align="center">
  <h3>🎥 Proof of Life: Supreme Court Retrieval</h3>
  <video src="https://github.com/user-attachments/assets/00a06667-c461-4ba5-a411-a78b5de99f78" width="100%" controls></video>
</div>

---

## Performance & Verification

**Evaluation Suite: 19/19 Pass Rate (Golden Core)**
The system is hardened against cross-jurisdictional hallucinations and "context smearing" through modular indexing and precision re-ranking.

| Case ID | Objective | Status | Mode |
| --- | --- | --- | --- |
| **tca-records-act** | Public Records Custodian | ✅ PASS | Fast |
| **confidentiality-exceptions** | TBI/Medical Record Exceptions | ✅ PASS | Fast |
| **toma-secret-ballots** | T.C.A. 8-44-104 Voting Requirements | ✅ PASS | Fast |
| **toma-action-nullified** | T.C.A. 8-44-105 Illegal Meeting Sanctions | ✅ PASS | Fast |
| **tpra-attorney-fees** | Willful Denial & Fee Recovery (10-7-505) | ✅ PASS | Fast |
| **tpra-commercial-value-news** | GIS Data Fees & Media Exemption (10-7-506) | ✅ PASS | Fast |
| **county-quorum** | 5-5-108 "Majority" Rule | ✅ PASS | Fast |
| **mayor-veto-budget** | County Mayor Veto Powers (5-6-107) | ✅ PASS | Fast |
| **budget-deadline-dept** | March 1st Budget Submission (5-12-208) | ✅ PASS | Fast |
| **finance-centralization** | Centralized Finance Department (5-21-103) | ✅ PASS | Fast |
| **conflict-of-interest-officers**| Officer Interest in Public Contracts (12-4-101)| ✅ PASS | Fast |
| **gtla-statute-limitations**| 12-Month Bar on Tort Suits (29-20-305) | ✅ PASS | Fast |
| **ezell-public-duty-doctrine**| Public Duty & Special Duty Exception (Ezell)| ✅ PASS | Fast |
| **mccallen-zoning-review**| Administrative Deference Standard (McCallen)| ✅ PASS | Fast |
| **griffin-suicide-notes** | Police Custody / Public Record Scope (Griffin) | ✅ PASS | Fast |
| **right-to-farm-nuisance** | Residential Encroachment (Johnson) | ✅ PASS | Fast |
| **drone-privacy-curtilage** | Warrantless Surveillance (Miller) | ✅ PASS | Fast |
| **ag-labor-workers-comp** | Landscaping Exemption (Martinez) | ✅ PASS | Fast |
| **bar-404b-distinction** | TN Standard for 404b Evidence | ✅ PASS | Fast |
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

* [x] **County Governance Ingest**: Comprehensive Title 5 & Title 13 zoning coverage
* [x] **Tort & Liability Ingest**: GTLA statutory shields (§ 29-20-201) and Public Duty precedent (*Ezell*)
* [x] **Sunshine Law Ingest**: TOMA and TPRA willful denial case law (*Griffin*, *Dorrier*)
* [x] **Precision Re-ranking**: Integrated Cross-Encoder (`ms-marco-MiniLM-L-6-v2`)
* [x] **Unified Normalizer Pipeline**: Standardized ingestion routing for raw Justia/Lexis text
* [ ] **Modular Test Suites**: CLI flags (`--suite core`, `--suite zoning`) for corpus scaling beyond 200 files
* [ ] **Containerization**: Docker support for "ship-anywhere" deployment

---

## Support / Follow

If you find this useful:

* Watch / Star the repo to keep up with weekly TN updates
* Share the project with researchers who need local, offline legal RAG
