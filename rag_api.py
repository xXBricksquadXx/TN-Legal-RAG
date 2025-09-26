from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import os, time
import requests
import chromadb
from chromadb.utils import embedding_functions

# ----------------------- Config -----------------------
EMB_MODEL   = os.getenv("EMBED_MODEL", "all-MiniLM-L6-v2")
OLLAMA_MODEL= os.getenv("OLLAMA_MODEL", "qwen2.5:1.5b-instruct")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
OLLAMA_URL  = f"{OLLAMA_HOST}/api/generate"

TOP_K               = int(os.getenv("TOP_K", "3"))
MIN_SIM_THRESHOLD   = float(os.getenv("MIN_SIM", "0.25"))  # 1 - cosine_distance; 0.25≈ good first gate
MAX_TOKENS_DEFAULT  = int(os.getenv("MAX_TOKENS", "256"))

# ----------------------- Embeddings & DB -----------------------
ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=EMB_MODEL, device=None)
client = chromadb.PersistentClient(path=".chroma")
try:
    collection = client.get_collection("personal", embedding_function=ef)
except Exception:
    collection = client.create_collection("personal", embedding_function=ef)

# ----------------------- FastAPI -----------------------
app = FastAPI()

class Query(BaseModel):
    q: str
    k: int = TOP_K
    max_tokens: int = MAX_TOKENS_DEFAULT

PROMPT_TEMPLATE = (
    "You are a careful assistant. Use ONLY the context below. If the answer is not fully "
    "supported by the context, reply exactly: Not in docs.\n\n"
    "Context:\n{context}\n\n"
    "Question: {q}\n\n"
    "Answer:"
)

def _ollama_complete(prompt: str, max_tokens: int) -> str:
    """One-shot non-streaming completion with small retry and safe timeout."""
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "options": {
            "num_predict": max_tokens,
            "temperature": 0,
        },
        "stream": False,
    }
    last_err = None
    for _ in range(3):
        try:
            r = requests.post(OLLAMA_URL, json=payload, timeout=60)
            r.raise_for_status()
            return (r.json().get("response") or "").strip()
        except requests.RequestException as e:
            last_err = e
            time.sleep(0.8)
    raise last_err or RuntimeError("Ollama call failed")

@app.get("/health")
def health():
    # light-touch reachability; don’t block startup if Ollama is down
    ok = True
    try:
        requests.get(f"{OLLAMA_HOST}/api/tags", timeout=5)
    except Exception:
        ok = False
    return {"ok": ok, "model": OLLAMA_MODEL}

@app.post("/query")
def query(body: Query):
    # include distances & metadatas; Chroma returns cosine distance (0=identical, 2=opposite) -> sim≈1-d
    res = collection.query(
        query_texts=[body.q],
        n_results=max(1, body.k),
        include=["documents", "metadatas", "distances", "ids"],
    )
    docs       = (res.get("documents") or [[]])[0]
    metas      = (res.get("metadatas") or [[]])[0]
    ids        = (res.get("ids") or [[]])[0]
    distances  = (res.get("distances") or [[]])[0]

    # Filter low-confidence hits
    kept = []
    for d, m, i, dist in zip(docs, metas, ids, distances):
        sim = 1.0 - float(dist)
        if sim >= MIN_SIM_THRESHOLD:
            kept.append((d, m or {}, i, sim))

    if not kept:
        return {
            "answer": "Not in docs.",
            "retrieved_docs_count": 0,
            "sources": [],
            "model": OLLAMA_MODEL,
        }

    # Build a compact, labeled context: [S1] text … with origin file displayed in sources
    lines = []
    srcs  = []
    for n, (d, m, i, sim) in enumerate(kept, start=1):
        src = m.get("source") or i
        lines.append(f"[S{n}] {d}")
        srcs.append({"id": i, "source": src, "sim": round(sim, 3)})
    context = "\n\n".join(lines)

    prompt = PROMPT_TEMPLATE.format(context=context, q=body.q)
    answer = _ollama_complete(prompt, body.max_tokens)
    return {
        "answer": answer,
        "retrieved_docs_count": len(kept),
        "sources": srcs,
        "model": OLLAMA_MODEL,
    }

@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    os.makedirs("docs", exist_ok=True)
    path = os.path.join("docs", file.filename)
    content = await file.read()
    text = content.decode("utf-8", errors="ignore").strip()
    if not text:
        return {"ok": False, "error": "Empty/unsupported file"}
    with open(path, "w", encoding="utf-8", errors="ignore") as f:
        f.write(text)
    # add full doc (the indexer will produce better chunked coverage; this keeps upload instant)
    collection.add(ids=[path], documents=[text], metadatas=[{"source": path}])
    return {"ok": True, "id": path, "bytes": len(content)}

@app.post("/forget")
def forget(doc_id: str = Form(...)):
    try:
        collection.delete(ids=[doc_id])
        try:
            os.remove(doc_id)
        except Exception:
            pass
        return {"ok": True, "deleted": doc_id}
    except Exception as e:
        return {"ok": False, "error": str(e)}

INDEX_HTML = """<!doctype html>
<html><head><meta charset="utf-8"><title>Private RAG</title>
<style>
body{font:16px system-ui;margin:24px;max-width:900px}
input,button,textarea{font:inherit}
#answer{white-space:pre-wrap;padding:12px;border:1px solid #ddd;border-radius:8px;margin-top:8px}
#sources{font-size:14px;color:#555;margin-top:4px}
</style></head><body>
<h1>Private RAG</h1>
<form id="ask">
  <input id="q" placeholder="Ask your docs…" style="width:100%;padding:10px;border-radius:8px;border:1px solid #ccc">
  <button style="margin-top:10px">Ask</button>
</form>
<div id="answer"></div><div id="sources"></div>
<hr>
<h3>Upload .txt/.md</h3>
<input type="file" id="file"><button id="up">Upload</button>
<pre id="upres"></pre>
<hr>
<h3>Forget a doc</h3>
<input id="docid" placeholder="docs/filename.txt" style="width:100%">
<button id="del">Delete</button>
<script>
async function postJSON(url, data){
  const r = await fetch(url,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(data)});
  return await r.json();
}
document.getElementById('ask').addEventListener('submit', async (e)=>{
  e.preventDefault();
  const q = document.getElementById('q').value;
  const j = await postJSON('/query', {q:q, k:3});
  document.getElementById('answer').textContent = j.answer || '(no answer)';
  const srcs = (j.sources||[]).map(s => `${s.source} (sim ${s.sim})`).join(', ');
  document.getElementById('sources').textContent = 'sources: ' + (srcs || '—');
});
document.getElementById('up').onclick = async ()=>{
  const f = document.getElementById('file').files[0];
  if(!f) { alert('Pick a file'); return; }
  const fd = new FormData(); fd.append('file', f);
  const r = await fetch('/upload', {method:'POST', body:fd});
  const j = await r.json();
  document.getElementById('upres').textContent = JSON.stringify(j, null, 2);
};
document.getElementById('del').onclick = async ()=>{
  const id = document.getElementById('docid').value;
  const fd = new FormData(); fd.append('doc_id', id);
  const r = await fetch('/forget', {method:'POST', body:fd});
  const j = await r.json();
  alert(JSON.stringify(j));
};
</script></body></html>
"""
@app.get("/", response_class=HTMLResponse)
def home():
    return INDEX_HTML
