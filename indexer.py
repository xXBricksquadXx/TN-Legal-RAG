import os
import glob
from pathlib import Path
from typing import Dict, Tuple, List

import chromadb
from sentence_transformers import SentenceTransformer


# ---- config (env) ----
CHROMA_DIR   = os.environ.get("CHROMA_DIR", ".chroma")
COLLECTION   = os.environ.get("CHROMA_COLLECTION", "tn_legal")
EMBED_MODEL  = os.environ.get("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

DOC_GLOB     = os.environ.get("DOC_GLOB", "docs/**/*.md")
MAX_CHARS    = int(os.environ.get("INDEX_MAX_CHARS", "900"))   # chunk size
OVERLAP      = int(os.environ.get("INDEX_OVERLAP",   "150"))   # overlap chars


# ---- helpers ----
def recreate_collection(client: chromadb.Client) -> chromadb.api.models.Collection.Collection:
    """Rebuild the collection with explicit cosine metric to match ST embeddings."""
    try:
        client.delete_collection(COLLECTION)
    except Exception:
        pass
    return client.create_collection(name=COLLECTION, metadata={"hnsw:space": "cosine"})


def parse_frontmatter(text: str) -> Tuple[Dict[str, str], str]:
    """Very small front-matter parser (YAML-ish, key: value)."""
    if text.startswith("---"):
        end = text.find("\n---", 4)
        if end != -1:
            meta: Dict[str, str] = {}
            for line in text[4:end].splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    meta[k.strip()] = v.strip().strip('"')
            body = text[end + 4 :].strip()
            return meta, body
    return {}, text


def chunk_text(text: str, max_chars: int, overlap: int) -> List[str]:
    """Chunk with character overlap, trying not to cut words too awkwardly."""
    out: List[str] = []
    i = 0
    n = len(text)
    if n <= max_chars:
        return [text.strip()] if text.strip() else []

    while i < n:
        j = min(n, i + max_chars)
        if j < n:
            # try to break at last whitespace before j
            k = text.rfind(" ", i + int(max_chars * 0.6), j)
            if k != -1:
                j = k
        out.append(text[i:j].strip())
        if j >= n:
            break
        i = max(0, j - overlap)
    return [c for c in out if c]


def main() -> None:
    print(f"Embedding model: {EMBED_MODEL}")
    embedder = SentenceTransformer(EMBED_MODEL)

    client = chromadb.PersistentClient(path=CHROMA_DIR)
    coll = recreate_collection(client)

    files = sorted(glob.glob(DOC_GLOB, recursive=True))
    total_chunks = 0

    for path in files:
        p = Path(path)
        raw = p.read_text(encoding="utf-8", errors="replace")
        meta, body = parse_frontmatter(raw)
        if not body.strip():
            continue

        chunks = chunk_text(body, MAX_CHARS, OVERLAP)
        if not chunks:
            continue

        embeddings = embedder.encode(chunks, normalize_embeddings=True)

        n = len(chunks)
        ids = [f"{path}::chunk{idx:04d}" for idx in range(n)]
        metadatas = []
        for idx in range(n):
            m = {
                "source": path,
                "chunk": idx,
                "n_chunks": n,
            }
            # carry selected front-matter into metadata
            for k in ("jurisdiction", "topic", "version_date", "doc_id", "citation", "source_url"):
                if k in meta:
                    m[k] = meta[k]
            metadatas.append(m)

        coll.add(ids=ids, documents=chunks, embeddings=embeddings, metadatas=metadatas)
        total_chunks += n

    print(f"Indexed {total_chunks} chunks from {len(files)} files -> {CHROMA_DIR}")


if __name__ == "__main__":
    main()
