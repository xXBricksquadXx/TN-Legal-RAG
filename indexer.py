import os, glob, re, json, time
from pathlib import Path
from typing import List, Dict, Generator
import chromadb
from chromadb.utils import embedding_functions

# CONFIG
DATA_DIR   = "docs"
CHROMA_DIR = ".chroma"
COLLECTION = "tn_legal"
EMB_MODEL  = "all-MiniLM-L6-v2"

def split_into_modular_chunks(text: str, max_chars: int = 1500) -> List[str]:
    """
    Modularizes by header to prevent context 'smear'.
    Ensures logical units like 10-7-504(a)(2) stay intact.
    """
    sections = re.split(r'\n(?=#{1,3} )', text)
    chunks = []
    for section in sections:
        section = section.strip()
        if not section: continue
        if len(section) > max_chars:
            # Secondary split on double-newline for safety
            paras = [p.strip() for p in re.split(r"\n\s*\n", section) if p.strip()]
            buf, size = [], 0
            for p in paras:
                if size + len(p) <= max_chars:
                    buf.append(p); size += len(p)
                else:
                    if buf: chunks.append("\n\n".join(buf))
                    buf, size = [p], len(p)
            if buf: chunks.append("\n\n".join(buf))
        else:
            chunks.append(section)
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
    print(">>> MISSION START: TN-LEGAL-RAG MODULAR INDEXER")
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=EMB_MODEL)
    
    try: client.delete_collection(COLLECTION)
    except: pass
    col = client.create_collection(COLLECTION, embedding_function=ef)

    files = glob.glob(f"{DATA_DIR}/**/*.md", recursive=True) + glob.glob(f"{DATA_DIR}/**/*.txt", recursive=True)

    for path in files:
        raw_txt = Path(path).read_text(encoding="utf-8", errors="ignore")
        fm = parse_front_matter(raw_txt)
        clean_txt = re.sub(r"^---\s*\n.*?\n---\s*\n", "", raw_txt, flags=re.S).strip()
        
        chunks = split_into_modular_chunks(clean_txt)
        
        # --- LOGGING BLOCK: MISSION RECAP ---
        file_name = os.path.basename(path)
        print(f"|-- [INDEXING] {file_name: <40} | Chunks: {len(chunks)}")
        
        for i, ch in enumerate(chunks):
            header_match = re.search(r'^#{1,3}\s+(.*)', ch)
            sub_label = header_match.group(1) if header_match else "General"
            
            # Sub-module tracking for 10-7-504 precision
            if "10-7-504" in file_name:
                print(f"    |-- Sub-Module: {sub_label[:30]}...")

            col.add(
                ids=[f"{path}_{i}"],
                documents=[ch],
                metadatas=[{
                    "source": path.replace("\\", "/"),
                    "topic": fm.get("topic", "code"),
                    "jurisdiction": fm.get("jurisdiction", "TN"),
                    "title": fm.get("title", ""),
                    "citation": fm.get("citation", ""),
                    "module": sub_label
                }]
            )
            
    print(">>> MISSION COMPLETE: Corpus vectorized and modularized.")

if __name__ == "__main__":
    main()