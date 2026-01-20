import os
import re
from pathlib import Path

# Config
RAW_DIR = "docs/raw_imports"
CLEAN_DIR = "docs/tn/code"

def clean_justia_text(text):
    """Strips web scaffolding and preserves core law."""
    text = re.sub(r"2024 Tennessee Code", "", text)
    text = re.sub(r"Universal Citation:.*?\n", "", text)
    text = re.sub(r"Learn more", "", text, flags=re.IGNORECASE)
    text = re.sub(r"Previous\s*\|\s*Next", "", text)
    text = re.sub(r"Acts \d{4},.*", "", text) # Remove citations at bottom
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

def get_metadata(filename):
    """Maps TCA chapter to RAG topic."""
    if "tca-5-5" in filename: return "county_legislative"
    if "tca-5-6" in filename: return "county_executive"
    if "tca-5-9" in filename or "tca-5-12" in filename: return "county_finance"
    if "tca-10-7" in filename: return "sunshine"
    return "statute"

def main():
    Path(CLEAN_DIR).mkdir(parents=True, exist_ok=True)
    for file_path in Path(RAW_DIR).glob("*.md"):
        print(f">>> Normalizing: {file_path.name}")
        raw_content = file_path.read_text(encoding="utf-8")
        clean_body = clean_justia_text(raw_content)
        topic = get_metadata(file_path.name)
        
        normalized = f"""---
title: {file_path.stem.upper()}
topic: {topic}
jurisdiction: TN
---
{clean_body}
"""
        target = Path(CLEAN_DIR) / file_path.name
        target.write_text(normalized)
        print(f"    Done -> {topic}")

if __name__ == "__main__":
    main()