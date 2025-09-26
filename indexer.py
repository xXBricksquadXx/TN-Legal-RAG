import os, glob, math
import chromadb
from chromadb.utils import embedding_functions
from typing import List, Tuple

EMB_MODEL = "all-MiniLM-L6-v2"
CHUNK_SIZE = 800
CHUNK_OVERLAP = 120

def _chunk_text(t: str, size=CHUNK_SIZE, overlap=CHUNK_OVERLAP) -> List[str]:
    t = " ".join(t.split())  # normalize whitespace
    if len(t) <= size:
        return [t]
    chunks = []
    start = 0
    while start < len(t):
        end = min(len(t), start + size)
        chunks.append(t[start:end])
        if end == len(t):
            break
        start = max(0, end - overlap)
    return chunks

def _load_and_chunk(root="docs") -> Tuple[List[str], List[str], List[dict]]:
    ids, docs, metas = [], [], []
    for p in glob.glob(os.path.join(root, "**", "*"), recursive=True):
        if not os.path.isfile(p):
            continue
        try:
            with open(p, "r", encoding="utf-8", errors="ignore") as f:
                txt = f.read().strip()
        except Exception:
            continue
        if not txt:
            continue
        chs = _chunk_text(txt)
        for i, ch in enumerate(chs):
            cid = f"{p}#chunk-{i:04d}"
            ids.append(cid)
            docs.append(ch)
            metas.append({"source": p, "chunk": i})
    return ids, docs, metas

def main():
    os.makedirs(".chroma", exist_ok=True)
    client = chromadb.PersistentClient(path=".chroma")

    # reset collection idempotently
    try:
        client.delete_collection("personal")
    except Exception:
        pass

    ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=EMB_MODEL, device=None)
    col = client.create_collection("personal", embedding_function=ef)

    ids, docs, metas = _load_and_chunk("docs")
    if not ids:
        print("No files found in ./docs. Add some .txt/.md and re-run.")
        return
    col.add(ids=ids, documents=docs, metadatas=metas)
    print(f"Indexed {len(ids)} chunks from {len(set(m['source'] for m in metas))} files → ./.chroma")

if __name__ == "__main__":
    main()
