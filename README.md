# TN-Legal-RAG

<img width="1536" height="1024" alt="TN-Legal-RAG Hero" src="https://github.com/user-attachments/assets/f378d568-c1ee-4a50-879c-487105163652" />

### Precision Retrieval for Tennessee Statutes & Regulations

**TN-Legal-RAG** is a mission-focused, private RAG (Retrieval-Augmented Generation) system designed for legal professionals and researchers. It provides grounded, citeable answers from a localized corpus including the Tennessee Code Annotated (TCA), Administrative Rules, and specialized Appellate/Supreme Court case law.

---

## Living Change Log

### Latest verified run (2026-08-10)

* **Corpus:** `138 files` indexed via **Modular Chunking** (`python3 indexer.py`) — *Added Law Enforcement & Finance package: Sheriff Duties (§ 8-8-201), Jail Medical Care (§ 41-4-115), GTLA Motor Vehicle Exception (§ 29-20-202), Competitive Bidding Thresholds (§ 12-3-1212), Booking Audits (§ 8-4-115), Tax Sales (§ 67-5-2501), Zoning Enforcement (§ 13-7-111), Shared Municipal Powers (§ 5-1-118), and SC precedents (Smith County Educ. Ass'n v. Anderson, Haynes v. Hamilton County).*
* **Interface & Prompt Hardening:** Upgraded glassmorphism UI layout with an expanded, scroll-free response window (`min-h-[22rem]`) and formatted text wrapping. Hardened LLM system prompt to enforce complete context-chunk scanning, removing single-chunk synthesis bottlenecks on 1.5B parameters.
* **Architecture Security:** WSL-to-Windows GPU Bridging patched to support dynamic Hyper-V IP shifting (Port 11434). Python environment isolated and re-sterilized.
* **Verification workflow:** `./scripts/check_all.sh`
  * Rebuilt index: **Verified (Header-Aware)**
  * API health check: **OK** (120-attempt window for Cross-Encoder initialization)
  * Smoke test: **OK** (TOMA, TPRA, & GTLA hallucination checks passed)
  * API eval: **19/19 passed** (FAST mode, workers=8) — **100% Golden Core pass rate**

#### Snapshot outputs (sanity checks)

* **High-Speed Pursuit Liability (Haynes v. Hamilton County)**
  * Output: `"A police officer's decision to initiate or continue a high-speed chase can constitute negligent 'conduct' that serves as the proximate cause of injuries to an innocent third party. Under Haynes, the county does not retain absolute GTLA immunity if the officer's unreasonable pursuit triggers the suspect's dangerous flight."`
  * Sources: `docs/tn/opinions/sc/haynes_v_hamilton_county.md`, `docs/tn/code/tca-29-20-202-negligent-operation-motor-vehicles.md`

* **Attorney-Client Exception to TOMA (Smith County Educ. Ass'n v. Anderson)**
  * Output: `"A county commission may meet privately behind closed doors with its legal counsel strictly to discuss pending or impending litigation without violating the Tennessee Open Meetings Act. However, any deliberation or decision-making regarding that litigation must occur in a public session."`
  * Sources: `docs/tn/opinions/sc/smith_county_educ_v_anderson.md`, `docs/tn/code/tca-8-44-101-policy-declaration.md`

* **Ouster Act Evidentiary Burden (State ex rel. Leech v. Wright)**
  * Output: `"An ouster proceeding under T.C.A. § 8-47-101 requires clear and convincing evidence of knowing or willful misconduct. Administrative incompetence, poor judgment, or simple mistakes without bad-faith intent do not justify forfeiture of public office."`
  * Sources: `docs/tn/opinions/sc/state-ex-rel-leech-v-wright.md`, `docs/tn/code/tca-8-47-101-officers-subject-to-removal.md`

---
<div align="center">
  <h3>🎥 Proof of Life: Supreme Court Retrieval</h3>
  <video src="https://github.com/user-attachments/assets/f3575fab-3dde-4793-b6a6-c8c2cb207945" width="100%" controls></video>
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
