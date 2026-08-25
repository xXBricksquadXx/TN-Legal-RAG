import os
import re
import requests
import chromadb
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional, List
from sentence_transformers import SentenceTransformer, CrossEncoder
from contextlib import asynccontextmanager
DB_PATH = "./.chroma"
COLLECTION_NAME = "tn_legal"
EMBED_MODEL_NAME = "all-MiniLM-L6-v2"
RERANK_MODEL_NAME = "cross-encoder/ms-marco-MiniLM-L-6-v2"
OLLAMA_URL = "http://172.22.144.1:11434/api/generate"
model = None
rerank_model = None
db_client = None
@asynccontextmanager
async def lifespan(app: FastAPI):
    global model, rerank_model, db_client
    print(">>> Initializing Models and Vector DB...")
    db_client = chromadb.PersistentClient(path=DB_PATH)
    model = SentenceTransformer(EMBED_MODEL_NAME)
    rerank_model = CrossEncoder(RERANK_MODEL_NAME)
    print(">>> System Hot. Re-ranker online.")
    yield
    print(">>> Shutting down.")
app = FastAPI(lifespan=lifespan)
class QueryRequest(BaseModel):
    q: str
    topic: Optional[str] = None
    k: int = 20      
    top_n: int = 5   
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
                min-height: 100vh;
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
            /* FIXED: Explicit high-contrast white text color for inputs */
            textarea { 
                background: rgba(0, 0, 0, 0.4) !important; 
                border: 1px solid rgba(255, 255, 255, 0.15) !important; 
                color: #ffffff !important; 
            }
            textarea::placeholder { color: #828a9a !important; }
        </style>
    </head>
    <body class="p-4 md:p-8">
        <div class="glass w-full max-w-5xl p-6 md:p-8">
            <div class="flex items-center mb-6">
                <span class="dot red"></span><span class="dot yellow"></span><span class="dot green"></span>
                <h1 class="text-white font-semibold text-lg ml-2">TN-Legal-RAG Interface</h1>
            </div>
            
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div class="flex flex-col">
                    <label class="text-xs uppercase tracking-widest text-gray-400 mb-2 block font-medium">Ask the Corpus</label>
                    <textarea id="query" rows="7" class="w-full p-4 rounded-xl focus:outline-none focus:ring-1 focus:ring-blue-500 text-sm leading-relaxed" placeholder="e.g., Did the GTLA abolish the public duty doctrine for police officers, and when does a special duty exist under Ezell?"></textarea>
                    <button onclick="ask()" class="mt-4 bg-white text-black font-bold py-3 px-6 rounded-xl hover:bg-gray-200 transition w-full shadow-lg text-sm">Search & Generate</button>
                </div>
                <div class="flex flex-col">
                    <label class="text-xs uppercase tracking-widest text-gray-400 mb-2 block font-medium">Response</label>
                    <div id="output" class="p-4 rounded-xl min-h-[22rem] max-h-[32rem] overflow-y-auto bg-black/40 text-gray-100 border border-white/10 text-sm leading-relaxed whitespace-pre-wrap">
                        <span class="text-gray-500 italic">Awaiting query...</span>
                    </div>
                </div>
            </div>

            <div class="mt-8">
                <label class="text-xs uppercase tracking-widest text-gray-400 mb-2 block font-medium">Retrieved Sources</label>
                <div id="sources" class="text-blue-400 text-sm flex flex-wrap gap-2"></div>
            </div>
        </div>

        <script>
           function formatMarkdown(text) {
                if (!text) return "";
                return text
                    .replace(/\\*\\*(.*?)\\*\\*/g, '<strong class="text-white font-semibold">$1</strong>')
                    .replace(/\\*(.*?)\\*/g, '<i class="text-gray-300">$1</i>')
                    .replace(/^- (.*)/gm, '• $1');
            }

            async function ask() {
                const q = document.getElementById('query').value;
                const out = document.getElementById('output');
                const srcDiv = document.getElementById('sources');
                out.innerHTML = "<span class='text-blue-400 animate-pulse'>Processing (Re-ranking & multi-chunk synthesis in progress)...</span>";
                srcDiv.innerHTML = "";

                try {
                    const res = await fetch('/query', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({q: q}) 
                    });
                    const data = await res.json();
                    
                    // Render cleaned HTML instead of raw stars
                    out.innerHTML = formatMarkdown(data.answer || data.error);
                    
                    if(data.sources && data.sources.length > 0) {
                        data.sources.forEach(s => {
                            const span = document.createElement('span');
                            span.className = "bg-blue-500/10 border border-blue-500/20 px-2.5 py-1.5 rounded-md text-xs font-mono text-blue-300";
                            span.innerText = s;
                            srcDiv.appendChild(span);
                        });
                    }
                } catch (err) {
                    out.innerHTML = "<span class='text-red-400'>Error connecting to server.</span>";
                }
            }
        </script>
    </body>
    </html>
    """
@app.post("/debug_query")
def debug_query(req: QueryRequest):
    try:
        coll = db_client.get_collection(COLLECTION_NAME)
        tca_match = re.search(r"(\d+-\d+-\d+)", req.q)
        retrieval_limit = 60 if tca_match else 40 
        q_emb = model.encode(req.q).tolist()
        results = coll.query(
            query_embeddings=[q_emb], 
            n_results=retrieval_limit
        )
        docs = results['documents'][0] if results['documents'] else []
        metas = results['metadatas'][0] if results['metadatas'] else []
        if not docs:
            return {"sources": [], "documents": [], "raw": {"documents": []}}
        pairs = [[req.q, doc] for doc in docs]
        scores = rerank_model.predict(pairs)
        ranked = sorted(zip(scores, docs, metas), key=lambda x: x[0], reverse=True)
        final_count = req.top_n if req.top_n <= len(ranked) else len(ranked)
        top_ranked = ranked[:final_count]
        return {
            "sources": list(set(r[2]['source'] for r in top_ranked)),
            "documents": [r[1] for r in top_ranked],
            "raw": {
                "documents": [r[1] for r in ranked] 
            }
        }
    except Exception as e:
        return {"error": str(e), "sources": [], "documents": [], "raw": {"documents": []}}
@app.post("/query")
def run_query(req: QueryRequest):
    data = debug_query(req)
    if "error" in data:
        return {"answer": f"API Error: {data['error']}", "sources": []}
    context = "\n---\n".join(data["documents"])
    prompt = (
        f"You are a Tennessee Legal Assistant. Ground your answer EXCLUSIVELY in the provided context.\n"
        f"INSTRUCTIONS:\n"
        f"1. Read ALL context blocks thoroughly before answering.\n"
        f"2. Synthesize information across different context blocks if required by the question.\n"
        f"3. Do not state that facts are missing unless you have checked every provided context block.\n"
        f"4. If the context mentions 'TPRA', it refers to the Tennessee Public Records Act.\n\n"
        f"Context:\n{context}\n\n"
        f"Question: {req.q}\n\n"
        f"Answer:"
    )
    try:
        r = requests.post(OLLAMA_URL, json={
            "model": "qwen2.5:1.5b-instruct", 
            "prompt": prompt, 
            "stream": False,
            "options": {"num_predict": req.max_tokens, "temperature": 0.0}
        })
        r.raise_for_status()
        return {"answer": r.json().get("response", ""), "sources": data["sources"]}
    except Exception as e:
        return {"answer": f"Ollama Connection Error: {str(e)}", "sources": data["sources"]}