import os
import re
from pathlib import Path

# Config
RAW_DIR = Path("docs/raw_imports")
STAGING_DIR = Path("docs/staging")
FINAL_CODE_DIR = Path("docs/tn/code")
FINAL_OPINION_DIR = Path("docs/tn/opinions")

def clean_text(text):
    """Unified cleaner for Justia/Lexis scaffolding."""
    text = re.sub(r"202[4-6] Tennessee Code", "", text)
    text = re.sub(r"Universal Citation:.*?\n", "", text)
    text = re.sub(r"Learn more|Previous\s*\|\s*Next", "", text, flags=re.IGNORECASE)
    text = re.sub(r"Acts \d{4},.*", "", text) 
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

def get_statute_meta(filename):
    if "tca-5" in filename.lower(): return "county_admin"
    if "tca-10" in filename.lower(): return "sunshine"
    return "statute"

def main():
    STAGING_DIR.mkdir(parents=True, exist_ok=True)
    
    for file_path in RAW_DIR.glob("*.md"):
        fname_lower = file_path.name.lower()
        # PRECISION FIX: Check for 'v', 'vs', 'opinion', or 'case' with underscores or spaces
        is_opinion = any(x in fname_lower.replace("_", " ") for x in [" v ", " vs ", "opinion", "case"])
        
        target_staging = STAGING_DIR / file_path.name
        final_dest = FINAL_OPINION_DIR if is_opinion else FINAL_CODE_DIR
        target_final = final_dest / file_path.name

        if target_final.exists():
            print(f"[-] Skipping {file_path.name}: Final version exists.")
            continue

        print(f"[+] Normalizing: {file_path.name} (Type: {'Opinion' if is_opinion else 'Statute'})")
        raw_content = file_path.read_text(encoding="utf-8")
        clean_body = clean_text(raw_content)

        if is_opinion:
            title_guess = file_path.stem.replace("_", " ").title()
            output = f"""---
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
{clean_body}
"""
        else:
            topic = get_statute_meta(file_path.name)
            doc_id = file_path.stem.upper()
            output = f"""---
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
        target_staging.write_text(output, encoding="utf-8")
        print(f"[#] Staged: {target_staging}")

if __name__ == "__main__":
    main()