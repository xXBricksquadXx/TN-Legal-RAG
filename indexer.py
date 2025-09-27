# indexer.py
import os, glob, re
from pathlib import Path
from typing import List, Tuple, Dict

import chromadb
from chromadb.utils import embedding_functions

# -------- config
DATA_DIR = "docs"
CHROMA_DIR = ".chroma"
COLLECTION = "personal"
EMB_MODEL = "all-MiniLM-L6-v2"  # sentence-transformers short model

# simple text splitter: paragraph blocks with a soft max char count
def split_into_chunks(text: str, max_chars: int = 900) -> List[str]:
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks: List[str] = []
    buf: List[str] = []
    size = 0
    for p in paras:
        if size + len(p) + 2 <= max_chars:
            buf.append(p); size += len(p) + 2
        else:
            if buf: chunks.append("\n\n".join(buf))
            buf, size = [p], len(p)
    if buf: chunks.append("\n\n".join(buf))
    return chunks

def load_files(root: str) -> List[str]:
    exts = (".txt", ".md")
    paths = []
    for p in glob.glob(os.path.join(root, "**", "*"), recursive=True):
        if os.path.isfile(p) and p.lower().endswith(exts):
            paths.append(p)
    return sorted(paths)

def build_payload(paths: List[str]) -> Tuple[List[str], List[str], List[Dict]]:
    ids, docs, metas = [], [], []
    for path in paths:
        try:
            txt = Path(path).read_text(encoding="utf-8", errors="ignore").strip()
        except Exception:
            continue
        if not txt:
            continue
        chunks = split_into_chunks(txt, max_chars=900)
        for i, ch in enumerate(chunks):
            cid = f"{path}::chunk{i:04d}"
            ids.append(cid)
            docs.append(ch)
            metas.append({"source": path, "chunk": i, "n_chunks": len(chunks)})
    return ids, docs, metas

def main():
    os.makedirs(CHROMA_DIR, exist_ok=True)
    client = chromadb.PersistentClient(path=CHROMA_DIR)

    # (re)create the collection
    try:
        client.delete_collection(COLLECTION)
    except Exception:
        pass

    ef = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=EMB_MODEL, device=None
    )
    col = client.create_collection(COLLECTION, embedding_function=ef)

    files = load_files(DATA_DIR)
    if not files:
        print(f"No .txt/.md in ./{DATA_DIR}. Add files and re-run.")
        return

    ids, docs, metas = build_payload(files)
    if not ids:
        print("Nothing to index (empty files?)")
        return

    col.add(ids=ids, documents=docs, metadatas=metas)
    print(f"Indexed {len(ids)} chunks from {len(files)} files → ./{CHROMA_DIR}")

if __name__ == "__main__":
    main()
