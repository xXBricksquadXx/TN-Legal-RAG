import os
import re
from pathlib import Path

DOCS_DIR = "docs"

def has_yaml(content):
    return content.strip().startswith("---")

def generate_meta(file_path):
    """Infents metadata based on the folder structure and filename."""
    parts = file_path.parts
    filename = file_path.name.replace(".md", "").upper()
    
    # Logic: if it's in docs/tn/code/tca-10... -> topic is 'sunshine'
    # If it's in docs/tn/bar/... -> topic is 'bar'
    topic = "general"
    if "code" in parts: topic = "statute"
    if "sunshine" in parts: topic = "sunshine"
    if "bar" in parts: topic = "bar"
    if "regs" in parts: topic = "regulations"

    return f"""---
title: {filename}
topic: {topic}
jurisdiction: TN
---
"""

def process_docs():
    count = 0
    for root, dirs, files in os.walk(DOCS_DIR):
        for file in files:
            if file.endswith(".md"):
                f_path = Path(root) / file
                content = f_path.read_text(encoding="utf-8")
                
                if not has_yaml(content):
                    print(f"Mirroring unity to: {f_path}")
                    meta = generate_meta(f_path)
                    f_path.write_text(meta + content, encoding="utf-8")
                    count += 1
    print(f"\n>>> Unity ♾️ achieved for {count} files.")

if __name__ == "__main__":
    process_docs()