import os
import requests
import chromadb
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional, List
from sentence_transformers import SentenceTransformer

app = FastAPI()

# Config
DB_PATH = "./.chroma"
COLLECTION = "tn_legal"
EMBED_MODEL = "all-MiniLM-L6-v2"
OLLAMA_URL = "http://localhost:11434/api/generate"

# Load Models
client = chromadb.PersistentClient(path=DB_PATH)
model = SentenceTransformer(EMBED_MODEL)

class QueryRequest(BaseModel):
    q: str
    topic: Optional[str] = None
    k: int = 4
    max_tokens: int = 512

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>TN Legal RAG</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <style>
            body { 
                background: radial-gradient(circle at top left, #1e1e2e, #11111b);
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                height: 100-vh;
                display: flex; justify-content: center; align-items: center;
            }
            .glass {
                background: rgba(255, 255, 255, 0.03);
                backdrop-filter: blur(12px);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 18px;
                box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.8);
            }
            .dot { height: 12px; width: 12px; border-radius: 50%; display: inline-block; margin-right: 6px; }
            .red { background: #ff5f56; } .yellow { background: #ffbd2e; } .green { background: #27c93f; }
            pre { font-size: 0.85rem; color: #a6adc8; }
            input, textarea { background: rgba(0,0,0,0.2); border: 1px solid rgba(255,255,255,0.1); color: white; }
        </style>
    </head>
    <body class="p-4 md:p-10">
        <div class="glass w-full max-w-4xl p-6">
            <div class="flex items-center mb-6">
                <span class="dot red"></span><span class="dot yellow"></span><span class="dot green"></span>
                <h1 class="text-white font-semibold ml-2">TN-Legal-RAG Interface</h1>
            </div>
            
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                    <label class="text-xs uppercase tracking-widest text-gray-400 mb-2 block">Ask the Corpus</label>
                    <textarea id="query" rows="4" class="w-full p-4 rounded-xl focus:outline-none focus:ring-1 focus:ring-blue-500" placeholder="e.g., What are the confidentiality exceptions for TBI?"></textarea>
                    <button onclick="ask()" class="mt-4 bg-white text-black font-bold py-2 px-6 rounded-lg hover:bg-gray-200 transition w-full">Search & Generate</button>
                </div>
                <div>
                    <label class="text-xs uppercase tracking-widest text-gray-400 mb-2 block">Response</label>
                    <div id="output" class="p-4 rounded-xl h-48 overflow-y-auto bg-black/30 text-gray-200 border border-white/5">
                        <span class="text-gray-500 italic">Awaiting query...</span>
                    </div>
                </div>
            </div>

            <div class="mt-8">
                <label class="text-xs uppercase tracking-widest text-gray-400 mb-2 block">Retrieved Sources</label>
                <div id="sources" class="text-blue-400 text-sm flex flex-wrap gap-2"></div>
            </div>
        </div>

        <script>
            async function ask() {
                const q = document.getElementById('query').value;
                const out = document.getElementById('output');
                const srcDiv = document.getElementById('sources');
                out.innerHTML = "Processing...";
                srcDiv.innerHTML = "";

                const res = await fetch('/query', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({q: q, k: 4})
                });
                const data = await res.json();
                out.innerHTML = data.answer || data.error;
                if(data.sources) {
                    data.sources.forEach(s => {
                        const span = document.createElement('span');
                        span.className = "bg-blue-500/10 border border-blue-500/20 px-2 py-1 rounded text-xs";
                        span.innerText = s;
                        srcDiv.appendChild(span);
                    });
                }
            }
        </script>
    </body>
    </html>
    """

@app.post("/debug_query")
def debug_query(req: QueryRequest):
    coll = client.get_collection(COLLECTION)
    q_emb = model.encode(req.q).tolist()
    results = coll.query(query_embeddings=[q_emb], n_results=req.k)
    return {
        "sources": list(set(m['source'] for m in results['metadatas'][0])),
        "raw": {"documents": results['documents'][0]}
    }

@app.post("/query")
def run_query(req: QueryRequest):
    debug_data = debug_query(req)
    context = "\n---\n".join(debug_data["raw"]["documents"])
    prompt = f"Context:\n{context}\n\nQuestion: {req.q}\n\nAnswer concisely using the context."
    r = requests.post(OLLAMA_URL, json={
        "model": "qwen2.5:1.5b-instruct", "prompt": prompt, "stream": False,
        "options": {"num_predict": req.max_tokens}
    })
    return {"answer": r.json().get("response", ""), "sources": debug_data["sources"]}