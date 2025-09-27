import os
from typing import Optional, List, Tuple

import requests
import chromadb
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer

# ---- config (env) ----
CHROMA_DIR         = os.environ.get("CHROMA_DIR", ".chroma")
CHROMA_COLLECTION  = os.environ.get("CHROMA_COLLECTION", "tn_legal")
EMBED_MODEL        = os.environ.get("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

TOP_K              = int(os.environ.get("TOP_K", "12"))
CTX_CHAR_LIMIT     = int(os.environ.get("CTX_CHAR_LIMIT", "6000"))
MAX_DISTANCE       = float(os.environ.get("MAX_DISTANCE", "0.85"))  # allow slightly wider cut
HYBRID_ALPHA       = float(os.environ.get("HYBRID_ALPHA", "0.6"))   # keyword boost weight

OLLAMA_HOST        = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")
OLLAMA_MODEL       = os.environ.get("OLLAMA_MODEL", "qwen2.5:1.5b-instruct")
OLLAMA_TEMPERATURE = float(os.environ.get("OLLAMA_TEMPERATURE", "0.1"))

# ---- single embedder instance ----
_embedder = SentenceTransformer(EMBED_MODEL)

app = FastAPI()

# ---- models ----
class Query(BaseModel):
    q: str
    k: Optional[int] = None
    topic: Optional[str] = None
    jurisdiction: Optional[str] = None
    max_tokens: Optional[int] = 512

# ---- helpers ----
def _collection():
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    # ensure cosine space to match sentence-transformers
    return client.get_or_create_collection(name=CHROMA_COLLECTION, metadata={"hnsw:space": "cosine"})

# terms that should boost TPRA fee questions
FEE_TERMS = [
    "$0.15", "0.15", "15 cents",
    "$0.50", "0.50", "50 cents",
    "labor threshold", "first hour", "first hour free", "first 1 hour",
    "copy charges", "per-page", "per page", "fee schedule", "schedule of reasonable charges",
    "lowest-paid qualified employee", "estimate", "cost estimate",
]

def _kw_score(text: str) -> float:
    t = text.lower()
    score = 0.0
    for term in FEE_TERMS:
        if term.lower() in t:
            score += 1.0
    return score

def _retrieve(q: str, k: int, topic: Optional[str], jurisdiction: Optional[str]) -> Tuple[List[str], List[dict], List[float]]:
    coll = _collection()
    qv = _embedder.encode([q], normalize_embeddings=True).tolist()[0]

    where = {}
    if topic:
        where["topic"] = {"$eq": topic}
    if jurisdiction:
        where["jurisdiction"] = {"$eq": jurisdiction}

    # pull wider then hybrid-rerank
    res = coll.query(
        query_embeddings=[qv],
        n_results=max(48, k),
        where=where if where else None,
        include=["documents", "metadatas", "distances"],
    )

    docs  = (res.get("documents") or [[]])[0]
    metas = (res.get("metadatas") or [[]])[0]
    dists = (res.get("distances") or [[]])[0]

    scored = []
    for d, m, dist in zip(docs, metas, dists):
        text = d or ""
        src = (m or {}).get("source", "")
        kw  = _kw_score(text + " " + src)
        score = -float(dist) + HYBRID_ALPHA * kw
        scored.append((score, d, m, dist))

    scored.sort(key=lambda x: x[0], reverse=True)
    top = scored[:k]

    out_docs  = [x[1] for x in top]
    out_metas = [x[2] for x in top]
    out_dists = [x[3] for x in top]
    return out_docs, out_metas, out_dists

def _build_prompt(q: str, docs: List[str], metas: List[dict], dists: List[float]) -> Tuple[str, List[str], List[float]]:
    kept_docs: List[str] = []
    kept_sources: List[str] = []
    kept_dists: List[float] = []
    total = 0
    for doc, meta, dist in zip(docs, metas, dists):
        if dist > MAX_DISTANCE:
            continue
        src = (meta or {}).get("source", "unknown")
        block = f"[Source: {os.path.basename(src)} | dist={dist:.2f}]\n{doc.strip()}\n\n"
        if total + len(block) > CTX_CHAR_LIMIT and kept_docs:
            break
        kept_docs.append(block)
        kept_sources.append(src)
        kept_dists.append(dist)
        total += len(block)

    header = (
        "You are a careful assistant. Answer ONLY using the provided context.\n"
        "If the answer is not fully supported by the context, reply exactly: Not in docs.\n\n"
    )
    prompt = header + "".join(kept_docs) + f"Question: {q}\n\nAnswer:"
    return prompt, kept_sources, kept_dists

def _ollama_complete(prompt: str, max_tokens: int = 512) -> str:
    try:
        r = requests.post(
            f"{OLLAMA_HOST}/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "options": {"temperature": OLLAMA_TEMPERATURE},
                "stream": False,
            },
            timeout=120,
        )
        r.raise_for_status()
        data = r.json()
        return data.get("response", "").strip() or "Not in docs"
    except Exception:
        return "Not in docs"

# ---- routes ----
@app.get("/health")
def health():
    return {
        "ok": True,
        "collection": CHROMA_COLLECTION,
        "model": OLLAMA_MODEL,
        "embed": EMBED_MODEL,
        "max_distance": MAX_DISTANCE,
        "hybrid_alpha": HYBRID_ALPHA,
    }

class DebugQuery(Query):
    pass

@app.post("/debug_query")
def debug_query(body: DebugQuery):
    k = body.k or TOP_K
    docs, metas, dists = _retrieve(body.q, k, body.topic, body.jurisdiction)
    prompt, sources, kept_dists = _build_prompt(body.q, docs, metas, dists)
    return {
        "ok": True,
        "query": body.q,
        "filters": {"topic": body.topic, "jurisdiction": body.jurisdiction},
        "raw_distances": dists,
        "threshold": MAX_DISTANCE,
        "prompt": prompt,
        "sources": sources,
        "raw": {"documents": docs, "metadatas": metas},
    }

@app.post("/query")
def query(body: Query):
    k = body.k or TOP_K
    docs, metas, dists = _retrieve(body.q, k, body.topic, body.jurisdiction)
    prompt, sources, kept_dists = _build_prompt(body.q, docs, metas, dists)
    if not sources:
        return {"answer": "Not in docs", "sources": [], "model": OLLAMA_MODEL, "threshold": MAX_DISTANCE}
    ans = _ollama_complete(prompt, max_tokens=body.max_tokens or 512)
    best = min(kept_dists) if kept_dists else None
    return {
        "answer": ans,
        "retrieved_docs_count": len(sources),
        "sources": sources,
        "model": OLLAMA_MODEL,
        "best_distance": best,
        "threshold": MAX_DISTANCE,
    }

@app.get("/", response_class=HTMLResponse)
def home():
    return """<!doctype html>
<html><body>
  <h1>TN-Legal-RAG</h1>
  <p>Endpoints:</p>
  <ul>
    <li><code>GET /health</code></li>
    <li><code>POST /debug_query</code> with {"q": "...", "topic":"sunshine"}</li>
    <li><code>POST /query</code> with {"q": "...", "topic":"sunshine"}</li>
  </ul>
</body></html>"""
