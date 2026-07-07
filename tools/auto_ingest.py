import os
import glob
import requests
import json
from pathlib import Path

# --- Configuration ---
RAW_DIR = Path("docs/raw_imports")
STAGING_DIR = Path("docs/staging")
OLLAMA_URL = "http://172.22.144.1:11434/api/generate"
MODEL = "qwen2.5:1.5b-instruct"

# Ensure directories exist
RAW_DIR.mkdir(parents=True, exist_ok=True)
STAGING_DIR.mkdir(parents=True, exist_ok=True)

PROMPT_TEMPLATE = """
You are an expert Tennessee Legal Data Architect. Your job is to take raw legal text (either a statute or a court opinion) and convert it into a perfectly formatted Markdown file using specific YAML metadata.

Raw Text:
{raw_text}

INSTRUCTIONS:
1. Extract the correct Title, Citation/Docket, and Jurisdiction.
2. Determine the 'topic'. You MUST choose exactly one of these: ['sunshine', 'opinions', 'county_finance', 'county_admin', 'county_legislative', 'bar']. DO NOT invent new topics. DO NOT wrap the topic string in brackets.
3. For the 'doc_id', create a lowercase, hyphen-separated slug of the citation and the title (e.g., 'tca-8-44-106-enforcement-jurisdiction').
4. Write a 1-2 sentence 'Practitioner Summary' explaining the impact of the text.
5. Extract 2-3 'Key Practice Points' as actionable bullet points.
6. Provide the 'Statutory Text' or 'Case Facts & Disposition' at the end. YOU MUST PASTE THE RAW TEXT VERBATIM. DO NOT SUMMARIZE OR REWRITE THE LAW.

OUTPUT FORMAT:
You MUST output ONLY the raw Markdown text. Do not include introductory conversational text. Start exactly with `---` and end with the text. DO NOT use ```markdown tags anywhere in your response.

Example Format:
---
title: 'T.C.A. § 8-44-106 — Enforcement - Jurisdiction'
jurisdiction: 'TN'
topic: 'sunshine'
citation: 'Tenn. Code Ann. § 8-44-106'
doc_id: 'tca-8-44-106-enforcement-jurisdiction'
---

## Practitioner Summary
[Your summary here]

## Key Practice Points
* **[Concept]**: [Explanation]

## Statutory Text
[PASTE THE RAW TEXT HERE VERBATIM - DO NOT SUMMARIZE - NO BACKTICKS]
"""

def process_file(file_path):
    print(f"[*] Processing: {file_path.name}")
    raw_text = file_path.read_text(encoding="utf-8")
    
    # Strip basic web junk before sending to LLM to save tokens
    raw_text = raw_text.replace("Universal Citation:", "")
    raw_text = raw_text.replace("Previous | Next", "")
    
    prompt = PROMPT_TEMPLATE.format(raw_text=raw_text)
    
    try:
        response = requests.post(OLLAMA_URL, json={
            "model": MODEL,
            "prompt": prompt,
            "stream": False,
            # INCREASED: Give the LLM 3000 tokens so it doesn't truncate long statutes
            "options": {"temperature": 0.1, "num_predict": 3000}
        }, timeout=600)
        response.raise_for_status()
        
        md_content = response.json().get("response", "").strip()
        
        # AGGRESSIVE SAFEGUARD: Nuke all markdown backticks
        md_content = md_content.replace("```markdown", "").replace("```", "").strip()
        
        # Try to extract doc_id for the filename
        doc_id = "unknown_doc"
        for line in md_content.splitlines():
            if line.startswith("doc_id:"):
                doc_id = line.split(":")[1].strip().strip("'").strip('"')
                break
        
        if doc_id == "unknown_doc" and "docket:" in md_content:
             doc_id = file_path.stem.lower().replace(" ", "_")
             
        out_file = STAGING_DIR / f"{doc_id}.md"
        out_file.write_text(md_content, encoding="utf-8")
        print(f"[+] Successfully staged: {out_file.name}")
        
    except Exception as e:
        print(f"[-] Error processing {file_path.name}: {e}")

def main():
    files = list(RAW_DIR.glob("*.txt")) + list(RAW_DIR.glob("*.md"))
    if not files:
        print("No raw files found in docs/raw_imports/")
        return
        
    for f in files:
        process_file(f)

if __name__ == "__main__":
    main()