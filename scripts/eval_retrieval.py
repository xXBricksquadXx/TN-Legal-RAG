#!/usr/bin/env python3
import sys, requests, yaml, concurrent.futures, time
from rich.console import Console
from rich.table import Table

API = "http://127.0.0.1:8000/debug_query"
TIMEOUT = 45
MAX_WORKERS = 6
console = Console()

def check(case):
    payload = {"q": case["q"], "topic": case.get("topic"), "k": case.get("k", 24)}
    try:
        r = requests.post(API, json=payload, timeout=TIMEOUT)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        return {"id": case.get("id"), "ok": False, "error": str(e), "sources": []}

    sources = data.get("sources") or []
    expects = case.get("expect_sources_any", [])
    ok = any(s in sources for s in expects)
    return {"id": case["id"], "ok": ok, "sources": sources[:10]}

def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("file", nargs="?", default="eval/cases.yaml")
    args = ap.parse_args()

    cases = yaml.safe_load(open(args.file))
    rel_cases = [c for c in cases if c.get("expect_sources_any")]
    console.print(f"[cyan]Running retrieval check on {len(rel_cases)} cases...[/cyan]")
    start = time.time()

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        results = list(ex.map(check, rel_cases))

    elapsed = time.time() - start
    passed = sum(1 for r in results if r["ok"])
    table = Table(title=f"Retrieval Checks ({passed}/{len(results)} passed, {elapsed:.1f}s)")
    table.add_column("Case ID", style="bold")
    table.add_column("Result")
    table.add_column("Top Sources")

    for r in results:
        if "error" in r:
            table.add_row(r["id"], "❌ (error)", r["error"])
        else:
            table.add_row(r["id"], "✅" if r["ok"] else "❌", ", ".join(r["sources"]))
    console.print(table)

    sys.exit(0 if passed == len(results) else 1)

if __name__ == "__main__":
    main()
