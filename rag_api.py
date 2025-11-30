from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import os, re, requests, traceback

import chromadb
from chromadb.utils import embedding_functions
from sentence_transformers import SentenceTransformer

# ========= config =========
DATA_DIR     = os.getenv("DATA_DIR", "docs")
CHROMA_DIR   = os.getenv("CHROMA_DIR", ".chroma")
COLLECTION   = os.getenv("CHROMA_COLLECTION", "tn_legal")
EMB_MODEL    = os.getenv("EMBED_MODEL", "all-MiniLM-L6-v2")

OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:1.5b-instruct")
OLLAMA_HOST  = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
OLLAMA_URL   = f"{OLLAMA_HOST}/api/generate"

HTTP_TIMEOUT = int(os.getenv("HTTP_TIMEOUT", "120"))
MAX_DISTANCE = float(os.getenv("MAX_DISTANCE", "0.75"))

# Warm the embedding model once (avoids first-call latency surprises)
_ = SentenceTransformer(EMB_MODEL)

# ========= chroma =========
client = chromadb.PersistentClient(path=CHROMA_DIR)
ef = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name=EMB_MODEL, device=None
)
try:
    collection = client.get_collection(COLLECTION, embedding_function=ef)
except Exception:
    collection = client.create_collection(COLLECTION, embedding_function=ef)

# ========= helpers =========
PROMPT_TEMPLATE = (
    "You are a careful assistant. Answer ONLY using the provided context.\n"
    "If the answer is not fully supported by the context, reply exactly: Not in docs.\n\n"
    "{context}\n\n"
    "Question: {q}\n\n"
    "Answer:"
)

def safe_list(x) -> List:
    # Cope with Chroma returning None / [] / [ [] ] / etc.
    if x is None:
        return []
    if isinstance(x, list):
        return x
    return []

def normalize_query_result(res) -> Tuple[List[str], List[Dict], List[str], List[float]]:
    docs_ll  = safe_list(res.get("documents"))
    metas_ll = safe_list(res.get("metadatas"))
    ids_ll   = safe_list(res.get("ids"))
    dists_ll = safe_list(res.get("distances"))

    docs  = safe_list(docs_ll[0])  if docs_ll  else []
    metas = safe_list(metas_ll[0]) if metas_ll else []
    ids   = safe_list(ids_ll[0])   if ids_ll   else []
    dists = safe_list(dists_ll[0]) if dists_ll else []
    return docs, metas, ids, dists

def format_context(
    docs: List[str], metas: List[Dict], dists: List[float], k: int
) -> str:
    """
    Build a context string from retrieved docs.

    1. Prefer docs within MAX_DISTANCE.
    2. If none are within threshold, fall back to the top-k docs anyway.
    """
    blocks: List[str] = []
    close_idxs: List[int] = []

    # First pass: collect indices within the distance threshold
    for i in range(min(k, len(docs))):
        try:
            dist_ok = (dists is None) or (i >= len(dists)) or (dists[i] <= MAX_DISTANCE)
        except Exception:
            dist_ok = True
        if dist_ok:
            close_idxs.append(i)

    # If nothing is within the threshold, fall back to the first k docs
    if not close_idxs:
        close_idxs = list(range(min(k, len(docs))))

    for i in close_idxs:
        src = (metas[i] or {}).get("source", "unknown") if i < len(metas) else "unknown"
        tag = Path(src).name
        dist_str = f"{dists[i]:.2f}" if (dists and i < len(dists)) else "?"
        blocks.append(f"[Source: {tag} | dist={dist_str}]\n{docs[i]}")

    return "\n\n---\n\n".join(blocks) if blocks else ""


def unique_sources(metas: List[Dict], ids: List[str]) -> List[str]:
    out = []
    for i, m in enumerate(metas or []):
        s = (m or {}).get("source")
        if not s and ids and i < len(ids):
            s = ids[i].split("::", 1)[0]
        if s and s not in out:
            out.append(s)
    return out

def ollama_complete(prompt: str, max_tokens: int) -> str:
    r = requests.post(
        OLLAMA_URL,
        json={
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "options": {
                "num_predict": max_tokens,
                "temperature": 0.1,
                "repeat_penalty": 1.1,
            },
            "stream": False,
        },
        timeout=HTTP_TIMEOUT,
    )
    r.raise_for_status()
    return (r.json() or {}).get("response", "").strip()

# ========= app =========
app = FastAPI(title="TN-Legal-RAG", version="0.5.1")

class Query(BaseModel):
    q: str
    k: int = 6
    max_tokens: int = 256
    topic: Optional[str] = None          # kept for future use
    jurisdiction: Optional[str] = None   # kept for future use

@app.get("/health")
def health():
    return {
        "ok": True,
        "collection": COLLECTION,
        "model": OLLAMA_MODEL,
        "embed": EMB_MODEL,
        "max_distance": MAX_DISTANCE,
    }

def _retrieve(q: str, k: int, topic: Optional[str], jurisdiction: Optional[str]):
    where = {}
    if topic:
        where["topic"] = topic
    if jurisdiction:
        where["jurisdiction"] = jurisdiction

    res = collection.query(
        query_texts=[q],
        n_results=max(1, int(k)),
        include=["documents", "metadatas", "distances"],
        where=where or None,
    )
    return normalize_query_result(res)



@app.post("/query")
def query(body: Query):
    try:
        docs, metas, ids, dists = _retrieve(body.q, body.k, body.topic, body.jurisdiction)
    except Exception as e:
        return JSONResponse(
            {"answer": "Not in docs", "error": f"retrieve failed: {e}"},
            status_code=200,
        )

    ctx = format_context(docs, metas, dists, body.k)
    if not ctx:
        return {
            "answer": "Not in docs",
            "sources": [],
            "model": OLLAMA_MODEL,
            "threshold": MAX_DISTANCE,
        }

    prompt = PROMPT_TEMPLATE.format(context=ctx, q=body.q)
    try:
        answer = ollama_complete(prompt, body.max_tokens)
    except Exception:
        return {
            "answer": "Not in docs (LLM offline).",
            "sources": unique_sources(metas, ids),
            "model": OLLAMA_MODEL,
            "threshold": MAX_DISTANCE,
        }

    answer = answer.strip() or "Not in docs"
    return {
        "answer": answer,
        "retrieved_docs_count": len(docs),
        "sources": unique_sources(metas, ids),
        "model": OLLAMA_MODEL,
        "best_distance": (
            min([d for d in dists if isinstance(d, (int, float))]) if dists else None
        ),
        "threshold": MAX_DISTANCE,
    }

@app.post("/debug_query")
def debug_query(body: Query):
    try:
        docs, metas, ids, dists = _retrieve(body.q, body.k, body.topic, body.jurisdiction)
        ctx = format_context(docs, metas, dists, body.k)
        return {
            "ok": True,
            "query": body.q,
            "filters": {"topic": body.topic, "jurisdiction": body.jurisdiction},
            "raw_distances": dists,
            "threshold": MAX_DISTANCE,
            "prompt": PROMPT_TEMPLATE.format(context=ctx, q=body.q),
            "sources": unique_sources(metas, ids),
            "raw": {"documents": docs, "metadatas": metas, "ids": ids},
        }
    except Exception as e:
        return JSONResponse(
            {
                "ok": False,
                "error": str(e),
                "trace": traceback.format_exc(limit=2),
            },
            status_code=200,
        )

@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    os.makedirs(DATA_DIR, exist_ok=True)
    path = os.path.join(DATA_DIR, file.filename)
    content = await file.read()
    text = content.decode("utf-8", errors="ignore").strip()
    if not text:
        return {"ok": False, "error": "Empty/unsupported file"}
    Path(path).write_text(text, encoding="utf-8", errors="ignore")

    # simple paragraph splitter
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks, buf, size = [], [], 0
    for p in paras:
        if size + len(p) + 2 <= 900:
            buf.append(p); size += len(p) + 2
        else:
            if buf: chunks.append("\n\n".join(buf))
            buf, size = [p], len(p)
    if buf: chunks.append("\n\n".join(buf))

    ids, docs, metas = [], [], []
    for i, ch in enumerate(chunks):
        ids.append(f"{path}::chunk{i:04d}")
        docs.append(ch)
        metas.append({"source": path, "chunk": i, "n_chunks": len(chunks)})

    if ids:
        collection.add(ids=ids, documents=docs, metadatas=metas)

    return {"ok": True, "id": path, "bytes": len(content), "chunks": len(ids)}

@app.post("/forget")
def forget(doc_id: str = Form(...)):
    try:
        if "::" not in doc_id:
            res = collection.get(where={"source": doc_id}, include=["ids"])
            ids = res.get("ids") or []
            if ids:
                collection.delete(ids=ids)
            Path(doc_id).unlink(missing_ok=True)
            return {"ok": True, "deleted": {"file": doc_id, "chunks": len(ids)}}
        else:
            collection.delete(ids=[doc_id])
            return {"ok": True, "deleted": {"chunk": doc_id}}
    except Exception as e:
        return {"ok": False, "error": str(e)}

# ========= minimal HTML UI =========
INDEX_HTML = """<!doctype html>
<html><head><meta charset="utf-8"><title>TN Legal RAG</title>
<style>
body{font:16px system-ui;margin:24px;max-width:880px}
input,button{font:inherit}
#answer{white-space:pre-wrap;padding:12px;border:1px solid #ddd;border-radius:8px;margin-top:8px}
#sources{font-size:14px;color:#555;margin-top:4px}
.small{font-size:12px;color:#777}
button{padding:8px 14px;border-radius:8px;border:1px solid #bbb;background:#f8f8f8;cursor:pointer}
input[type=text]{width:100%;padding:10px;border-radius:8px;border:1px solid #ccc}
hr{margin:20px 0}
</style></head><body>
<h1>TN Legal RAG</h1>
<form id="ask">
  <input id="q" type="text" placeholder="Ask TN regs / sunshine / budgets…">
  <button style="margin-top:10px">Ask</button>
</form>
<div id="answer"></div>
<div id="sources" class="small"></div>
<hr>
<h3>Upload .txt/.md</h3>
<input type="file" id="file"><button id="up">Upload</button>
<pre id="upres" class="small"></pre>
<hr>
<h3>Forget a doc</h3>
<input id="docid" type="text" placeholder="docs/filename.md or docs/file.md::chunk0003">
<button id="del">Delete</button>

<script>
function postJSON(url, data){
  return fetch(url,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(data)})
   .then(function(r){ if(!r.ok) throw new Error("HTTP "+r.status); return r.json(); });
}

(function(){
  var form = document.getElementById('ask');
  var qEl  = document.getElementById('q');
  var ans  = document.getElementById('answer');
  var srcs = document.getElementById('sources');

  form.addEventListener('submit', function(e){
    e.preventDefault();
    var q = (qEl.value || "").trim();
    if(!q){ ans.textContent="(enter a question)"; return; }
    ans.textContent = "Thinking…";
    srcs.textContent = "";
    postJSON('/query', {q:q, k:6, max_tokens:256})
      .then(function(j){
        ans.textContent = (j && j.answer) ? j.answer : "(no answer)";
        if(j && j.sources && j.sources.length){ srcs.textContent = "sources: " + j.sources.join(', '); }
      })
      .catch(function(err){ ans.textContent = "Error: " + err.message; });
  });

  document.getElementById('up').onclick = function(){
    var f = document.getElementById('file').files[0];
    if(!f) { alert('Pick a file'); return; }
    var fd = new FormData(); fd.append('file', f);
    fetch('/upload', {method:'POST', body:fd})
      .then(function(r){ return r.json(); })
      .then(function(j){ document.getElementById('upres').textContent = JSON.stringify(j, null, 2); })
      .catch(function(err){ alert("Upload error: " + err.message); });
  };

  document.getElementById('del').onclick = function(){
    var id = document.getElementById('docid').value;
    var fd = new FormData(); fd.append('doc_id', id);
    fetch('/forget', {method:'POST', body:fd})
      .then(function(r){ return r.json(); })
      .then(function(j){ alert(JSON.stringify(j)); })
      .catch(function(err){ alert("Delete error: " + err.message); });
  };
})();
</script>
</body></html>
"""

@app.get("/", response_class=HTMLResponse)
def home():
    return INDEX_HTML
