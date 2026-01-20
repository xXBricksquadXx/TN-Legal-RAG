import os
import re
from pathlib import Path

# Config
RAW_DIR = "docs/raw_imports"
STAGING_DIR = "docs/staging"
FINAL_DIR = "docs/tn/code"

def clean_justia_text(text):
    """Strips web scaffolding and preserves core law."""
    text = re.sub(r"2024 Tennessee Code", "", text)
    text = re.sub(r"Universal Citation:.*?\n", "", text)
    text = re.sub(r"Learn more", "", text, flags=re.IGNORECASE)
    text = re.sub(r"Previous\s*\|\s*Next", "", text)
    text = re.sub(r"Acts \d{4},.*", "", text) 
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

def get_metadata(filename):
    """Maps TCA chapter to RAG topic."""
    if "tca-5" in filename: return "county_admin"
    if "tca-10" in filename: return "sunshine"
    return "statute"

def main():
    # Ensure directories exist
    Path(STAGING_DIR).mkdir(parents=True, exist_ok=True)
    
    for file_path in Path(RAW_DIR).glob("*.md"):
        target_final = Path(FINAL_DIR) / file_path.name
        
        # SAFETY GUARD: Check if finalized file already has "The Meat"
        if target_final.exists():
            existing_content = target_final.read_text(encoding="utf-8")
            if "## Practitioner Summary" in existing_content:
                print(f"!!! Skipping {file_path.name}: Expert content already exists in FINAL_DIR.")
                continue

        print(f">>> Normalizing to Staging: {file_path.name}")
        raw_content = file_path.read_text(encoding="utf-8")
        clean_body = clean_justia_text(raw_content)
        topic = get_metadata(file_path.name)
        doc_id = file_path.stem.upper()
        
        # The Unity 2.0 Template
        normalized = f"""---
title: {doc_id}
topic: {topic}
jurisdiction: TN
---

## Practitioner Summary
> [MANUAL ENTRY REQUIRED]: Summarize the impact of this section.

## Key Practice Points
* ## Statutory Text
{clean_body}
"""
        target_staging = Path(STAGING_DIR) / file_path.name
        target_staging.write_text(normalized, encoding="utf-8")
        print(f"    Done -> {target_staging}")

if __name__ == "__main__":
    main()