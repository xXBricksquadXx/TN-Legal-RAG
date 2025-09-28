#!/usr/bin/env python3
import os, sys, chromadb
from pathlib import Path
from sentence_transformers import SentenceTransformer

CHROMA_DIR   = os.environ.get("CHROMA_DIR", ".chroma")
COLLECTION   = os.environ.get("CHROMA_COLLECTION", "tn_legal")
EMBED_MODEL  = os.environ.get("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

def parse_frontmatter(text: str):
    if text.startswith("---"):
        end = text.find("\n---", 4)
        if end != -1:
            meta = {}
            for line in text[4:end].splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    meta[k.strip()] = v.strip().strip('"')
            return meta, text[end+4:].strip()
    return {}, text

def chunk(text, max_chars=550, overlap=120):
    out=[]; i=0; n=len(text)
    while i < n:
        j=min(n, i+max_chars)
        if j<n:
            k=text.rfind("\n\n", i, j)
            if k==-1: k=text.rfind(" ", i, j)
            if k!=-1 and k>i+200: j=k
        out.append(text[i:j].strip())
        i = j-overlap if j<n else j
        if i<0: i=0
    return [s for s in out if s]

def main():
    if len(sys.argv)!=2:
        print("usage: upsert_md.py <path/to/file.md>", file=sys.stderr)
        sys.exit(2)
    p=Path(sys.argv[1])
    meta, body = parse_frontmatter(p.read_text(encoding="utf-8"))
    source = str(p)
    parts = chunk(body)
    ids = [f"{source}::chunk{idx:04d}" for idx,_ in enumerate(parts)]
    metas=[{**meta, "source":source, "chunk":i, "n_chunks":len(parts)} for i,_ in enumerate(parts)]

    emb = SentenceTransformer(EMBED_MODEL).encode(parts, convert_to_numpy=True).tolist()
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    coll = client.get_or_create_collection(COLLECTION, metadata={"hnsw:space":"cosine"})

    # delete old chunks for this source (if any), then upsert
    try:
        old = coll.get(where={"source":{"$eq":source}}, include=[])
        if old.get("ids"):
            coll.delete(ids=old["ids"])
    except Exception:
        pass

    coll.upsert(ids=ids, documents=parts, metadatas=metas, embeddings=emb)
    print(f"Upserted {len(parts)} chunks from {source}")

if __name__=="__main__":
    main()
