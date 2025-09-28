#!/usr/bin/env python3
import sys, requests, yaml

API = "http://127.0.0.1:8000/debug_query"

def check(case):
    payload = {"q": case["q"], "topic": case.get("topic"), "k": case.get("k",24)}
    r = requests.post(API, json=payload, timeout=60)
    r.raise_for_status()
    data = r.json()
    sources = data.get("sources") or []
    ok = any(s in sources[:case.get("k",24)] for s in case.get("expect_sources_any", []))
    return {"id": case["id"], "ok": ok, "sources": sources[:10]}

def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("file", nargs="?", default="eval/cases.yaml")
    args = ap.parse_args()
    cases = yaml.safe_load(open(args.file))
    rel_cases = [c for c in cases if c.get("expect_sources_any")]
    res = [check(c) for c in rel_cases]
    passed = sum(1 for r in res if r["ok"])
    print(f"Retrieval: {passed}/{len(res)} top-K source checks passed")
    for r in res:
        mark = "✅" if r["ok"] else "❌"
        print(f"{mark} {r['id']}  top sources: {r['sources']}")
    sys.exit(0 if passed==len(res) else 1)

if __name__ == "__main__":
    main()
