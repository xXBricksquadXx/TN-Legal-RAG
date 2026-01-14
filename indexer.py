import os, glob, re, json
from pathlib import Path
from typing import List, Tuple, Dict
import chromadb
from chromadb.utils import embedding_functions

DATA_DIR   = "docs"
CHROMA_DIR = ".chroma"
COLLECTION = "tn_legal"
EMB_MODEL  = "all-MiniLM-L6-v2"

def split_into_chunks(text: str, max_chars: int = 900) -> List[str]:
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks, buf, size = [], [], 0
    for p in paras:
        if size + len(p) + 2 <= max_chars:
            buf.append(p); size += len(p) + 2
        else:
            if buf: chunks.append("\n\n".join(buf))
            buf, size = [p], len(p)
    if buf: chunks.append("\n\n".join(buf))
    return chunks

def parse_front_matter(txt: str) -> Dict:
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", txt, re.S)
    meta = {}
    if m:
        block = m.group(1)
        for line in block.splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip()] = v.strip().strip('"').strip("'")
    return meta

def main():
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=EMB_MODEL)
    
    try: client.delete_collection(COLLECTION)
    except: pass
    col = client.create_collection(COLLECTION, embedding_function=ef)

    files = glob.glob(f"{DATA_DIR}/**/*.md", recursive=True) + glob.glob(f"{DATA_DIR}/**/*.txt", recursive=True)

    for path in files:
        raw_txt = Path(path).read_text(encoding="utf-8", errors="ignore")
        fm = parse_front_matter(raw_txt)
        # Clean text for chunking (remove FM block)
        clean_txt = re.sub(r"^---\s*\n.*?\n---\s*\n", "", raw_txt, flags=re.S).strip()
        
        chunks = split_into_chunks(clean_txt)
        for i, ch in enumerate(chunks):
            col.add(
                ids=[f"{path}_{i}"],
                documents=[ch],
                metadatas=[{
                    "source": path.replace("\\", "/"),
                    "topic": fm.get("topic", ""),
                    "jurisdiction": fm.get("jurisdiction", "TN"),
                }]
            )
    print(f">>> Indexed {len(files)} files.")

if __name__ == "__main__":
    main()