import os
import re
from pathlib import Path

RAW_DIR = "docs/raw_imports"
STAGING_DIR = "docs/staging"

def main():
    Path(STAGING_DIR).mkdir(parents=True, exist_ok=True)
    
    for file_path in Path(RAW_DIR).glob("*.md"):
        # Process anything flagged as an opinion or case
        if not any(x in file_path.name.lower() for x in ["opinion", "case", "vs"]):
            continue
            
        target_path = Path(STAGING_DIR) / file_path.name
        
        # SAFETY: Don't overwrite if you've already started the manual summary
        if target_path.exists():
            existing = target_path.read_text()
            if "## Practitioner Summary" in existing and "[ACTION]" not in existing:
                print(f"!!! Skipping {file_path.name}: Expert content detected in staging.")
                continue

        print(f">>> Normalizing Opinion: {file_path.name}")
        content = file_path.read_text(encoding="utf-8")
        
        # Draft a Title from filename if no clear title in text
        title_guess = file_path.stem.replace("_", " ").title()
        
        template = f"""---
title: '{title_guess}'
docket: 'PENDING'
opinion_date: '2026-01-01'
judge: 'TBD'
topic: 'opinions'
jurisdiction: 'TN_Supreme_Court'
tags: ['legal_opinion']
---

## Practitioner Summary
> [ACTION]: Provide high-level holding here.

## Key Practice Points
* ## Case Facts & Disposition
{content}
"""
        target_path.write_text(template, encoding="utf-8")
        print(f"    Staged for Review: {target_path}")

if __name__ == "__main__":
    main()