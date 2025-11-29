import os, glob, re, json
from pathlib import Path
from typing import List, Tuple, Dict

import chromadb
from chromadb.utils import embedding_functions

# -------- config (env-overridable)
DATA_DIR   = os.getenv("DATA_DIR", "docs")
CHROMA_DIR = os.getenv("CHROMA_DIR", ".chroma")
COLLECTION = os.getenv("CHROMA_COLLECTION", "tn_legal")
EMB_MODEL  = os.getenv("EMBED_MODEL", "all-MiniLM-L6-v2")  # sentence-transformers

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

def parse_front_matter(txt: str) -> Dict:
    """
    Supports simple YAML-style front-matter fenced by --- ... --- at the top.
    We parse it with a minimal regex to avoid adding a YAML dependency.
    """
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", txt, re.S)
    meta = {}
    if m:
        block = m.group(1)
        for line in block.splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip()] = v.strip().strip('"').strip("'")
    return meta

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

        fm = parse_front_matter(txt)
        chunks = split_into_chunks(txt, max_chars=900)
        for i, ch in enumerate(chunks):
            cid = f"{path}::chunk{i:04d}"
            ids.append(cid)
            docs.append(ch)
            metas.append({
                "source": path,
                "chunk": i,
                "n_chunks": len(chunks),
                # helpful filters:
                "topic": fm.get("topic", ""),
                "jurisdiction": fm.get("jurisdiction", ""),
                "version_date": fm.get("version_date", fm.get("accessed", "")),
            })
    return ids, docs, metas

def main():
    os.makedirs(CHROMA_DIR, exist_ok=True)
    client = chromadb.PersistentClient(path=CHROMA_DIR)

    ef = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=EMB_MODEL, device=None
    )

    # Get existing collection if it exists; otherwise create it
    try:
        col = client.get_collection(COLLECTION, embedding_function=ef)
        # Clear existing docs but keep the same collection id
        try:
            col.delete(where={})  # delete all docs
        except Exception:
            pass
    except Exception:
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

