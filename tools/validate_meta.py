#!/usr/bin/env python3
import sys, re, json
from pathlib import Path
from typing import Tuple, Dict, Optional

RE_FRONT = re.compile(r'^---\n(.*?)\n---\n', re.DOTALL)
RE_KV    = re.compile(r'^\s*([A-Za-z0-9_]+)\s*:\s*(.*)\s*$', re.M)
ALLOWED_TOPICS = {"sunshine","code","regs","budget","atty","bar"}

def parse_frontmatter(text:str) -> Tuple[Optional[Dict[str,str]], int]:
    m = RE_FRONT.match(text)
    if not m: return None, 0
    raw = m.group(1)
    meta = {}
    for line in raw.splitlines():
        if not line.strip() or line.strip().startswith("#"): continue
        m2 = RE_KV.match(line)
        if m2:
            k,v = m2.groups()
            v = v.strip()
            # strip surrounding quotes and trailing comments
            if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
                v = v[1:-1]
            v = v.split("#",1)[0].rstrip()
            meta[k] = v
    return meta, m.end()

def normalize_topic(v:str) -> str:
    # remove stray comment tails like:  sunshine"     # ...
    v = v.replace('"','').replace("'",'').strip()
    v = v.split("#",1)[0].strip()
    return v

def validate_file(p:Path, autofix:bool=False) -> Dict:
    txt = p.read_text(encoding="utf-8", errors="ignore")
    meta, end = parse_frontmatter(txt)
    errs, fixes = [], []
    if meta is None:
        return {"path":str(p), "ok":False, "errors":["missing front-matter '---'"], "fixes":[]}

    required = ["title","jurisdiction","topic"]
    for k in required:
        if k not in meta or not meta[k].strip():
            errs.append(f"missing required key: {k}")

    if "topic" in meta:
        t0 = meta["topic"]
        t  = normalize_topic(t0)
        if t != t0:
            fixes.append(f"topic normalized '{t0}' -> '{t}'")
            if autofix:
                meta["topic"] = t
        if t not in ALLOWED_TOPICS:
            errs.append(f"topic not in {sorted(ALLOWED_TOPICS)}: '{t}'")

    # light sanity on jurisdiction
    if "jurisdiction" in meta and meta["jurisdiction"] not in {"TN","US"}:
        fixes.append(f"non-standard jurisdiction: {meta['jurisdiction']}")

    # write back if fixing
    if autofix and fixes:
        # rebuild YAML exactly (quotes plain)
        lines = [f"{k}: \"{meta[k]}\"" for k in meta]
        new = "---\n" + "\n".join(lines) + "\n---\n" + txt[end:]
        p.write_text(new, encoding="utf-8")

    return {"path":str(p), "ok":not errs, "errors":errs, "fixes":fixes, "topic":meta.get("topic")}

def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--autofix", action="store_true", help="apply safe normalizations (topic/quotes)")
    ap.add_argument("--json", action="store_true", help="print JSON report")
    ap.add_argument("roots", nargs="*", default=["docs"])
    args = ap.parse_args()

    files = [p for r in args.roots for p in Path(r).rglob("*.md")]
    report = [validate_file(p, autofix=args.autofix) for p in sorted(files)]
    bad = [r for r in report if not r["ok"]]
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        for r in report:
            status = "OK " if r["ok"] else "ERR"
            fix = f"  fixes: {r['fixes']}" if r["fixes"] else ""
            err = f"  errors: {r['errors']}" if r["errors"] else ""
            print(f"[{status}] {r['path']}{fix}{err}")
        print(f"\nSummary: {len(report)-len(bad)}/{len(report)} OK, {len(bad)} files with errors.")
    sys.exit(0 if not bad else 2)

if __name__ == "__main__":
    main()
