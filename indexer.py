import os, glob
import chromadb
from chromadb.utils import embedding_functions

EMB_MODEL = "all-MiniLM-L6-v2"

def load_texts(root="docs"):
    ids, docs = [], []
    for p in glob.glob(os.path.join(root, "**", "*"), recursive=True):
        if os.path.isfile(p):
            try:
                with open(p, "r", encoding="utf-8", errors="ignore") as f:
                    txt = f.read().strip()
                    if txt:
                        ids.append(p)
                        docs.append(txt)
            except Exception:
                pass
    return ids, docs

def main():
    os.makedirs(".chroma", exist_ok=True)
    client = chromadb.PersistentClient(path=".chroma")

    # (re)create the collection idempotently
    try:
        client.delete_collection("personal")
    except Exception:
        pass

    ef = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=EMB_MODEL, device=None
    )
    col = client.create_collection("personal", embedding_function=ef)

    ids, docs = load_texts("docs")
    if not ids:
        print("No files found in ./docs. Add some .txt/.md and re-run.")
        return

    col.add(ids=ids, documents=docs)
    print(f"Indexed {len(ids)} docs → ./.chroma")

if __name__ == "__main__":
    main()
