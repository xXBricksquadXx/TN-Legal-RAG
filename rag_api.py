from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import chromadb
from chromadb.utils import embedding_functions
from sentence_transformers import SentenceTransformer
import requests, os

EMB_MODEL = "all-MiniLM-L6-v2"
_ = SentenceTransformer(EMB_MODEL)  # warm cache

# --- Chroma (new API)
client = chromadb.PersistentClient(path=".chroma")
ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=EMB_MODEL, device=None)
try:
    collection = client.get_collection("personal", embedding_function=ef)
except Exception:
    collection = client.create_collection("personal", embedding_function=ef)

# --- Ollama
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:1.5b-instruct")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434/api/generate")

app = FastAPI()

class Query(BaseModel):
    q: str
    k: int = 3
    max_tokens: int = 256

PROMPT_TEMPLATE = (
    "You are a careful assistant. Answer ONLY using the provided context. "
    "If the answer is not fully supported by the context, reply exactly: 'Not in docs.'\n\n"
    "Context:\n{context}\n\nQuestion: {q}\n\nAnswer:"
)

def ollama_complete(prompt: str, max_tokens: int) -> str:
    r = requests.post(
        OLLAMA_URL,
        json={"model": OLLAMA_MODEL, "prompt": prompt, "options": {"num_predict": max_tokens}, "stream": False},
        timeout=120,
    )
    r.raise_for_status()
    return r.json().get("response", "").strip()

@app.get("/health")
def health():
    return {"ok": True, "model": OLLAMA_MODEL}

@app.post("/query")
def query(body: Query):
    res = collection.query(query_texts=[body.q], n_results=body.k)
    docs = (res.get("documents") or [[]])[0]
    ids  = (res.get("ids") or [[]])[0]
    context = "\n\n---\n\n".join(docs)
    prompt = PROMPT_TEMPLATE.format(context=context, q=body.q)
    answer = ollama_complete(prompt, body.max_tokens)
    return {"answer": answer, "retrieved_docs_count": len(docs), "sources": ids, "model": OLLAMA_MODEL}

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
    collection.add(ids=[path], documents=[text])
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
body{font:16px system-ui;margin:24px;max-width:800px}
input,button,textarea{font:inherit}
#answer{white-space:pre-wrap;padding:12px;border:1px solid #ddd;border-radius:8px;margin-top:8px}
#sources{font-size:14px;color:#555}
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
  document.getElementById('sources').textContent = 'sources: ' + (j.sources||[]).join(', ');
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
