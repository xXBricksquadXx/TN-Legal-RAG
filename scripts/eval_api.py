#!/usr/bin/env python3
import sys, requests, yaml

API = "http://127.0.0.1:8000/query"

def run_case(case):
    payload = {"q": case["q"], "topic": case.get("topic")}
    r = requests.post(API, json=payload, timeout=60)
    r.raise_for_status()
    data = r.json()
    ans  = (data.get("answer") or "").lower()
    srcs = data.get("sources") or []

    ok_text = True
    if case.get("expect_contains"):
        ok_text = case["expect_contains"].lower() in ans
    if case.get("expect_contains_any"):
        opts = [s.lower() for s in case["expect_contains_any"]]
        ok_text = any(opt in ans for opt in opts)

    ok_src = True
    expects = case.get("expect_sources_any", [])
    if expects:
        ok_src = any(s in srcs for s in expects)

    return {
        "id": case.get("id"),
        "passed": ok_text and ok_src,
        "ok_text": ok_text,
        "ok_src": ok_src,
        "answer": data.get("answer"),
        "sources": srcs,
    }

def main():
    file = sys.argv[1] if len(sys.argv) > 1 else "eval/cases.yaml"
    cases = yaml.safe_load(open(file))
    results = [run_case(c) for c in cases]
    passed = sum(1 for r in results if r["passed"])
    print(f"\nResults: {passed}/{len(results)} passed\n")
    for r in results:
        mark = "✅" if r["passed"] else "❌"
        print(f"{mark} {r['id']}: text={r['ok_text']} src={r['ok_src']}")
        if not r["passed"]:
            print(f"  answer: {r['answer']}\n  sources: {r['sources']}")
if __name__ == "__main__":
    main()

