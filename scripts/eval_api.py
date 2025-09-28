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
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("file", nargs="?", default="eval/cases.yaml")
    args = ap.parse_args()

    cases = yaml.safe_load(open(args.file, "r", encoding="utf-8"))
    results = [run_case(c) for c in cases]

    passed = sum(1 for r in results if r["passed"])
    total  = len(results)
    print(f"\nResults: {passed}/{total} passed\n")

    for r in results:
        mark = "✅" if r["passed"] else "❌"
        print(f"{mark} {r['id']}: text={r['ok_text']} src={r['ok_src']}")
        if not r["passed"]:
            print(f"  answer:  {r['answer']}")
            print(f"  sources: {r['sources']}")

    sys.exit(0 if passed == total else 1)

if __name__ == "__main__":
    main()
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
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("file", nargs="?", default="eval/cases.yaml")
    args = ap.parse_args()

    cases = yaml.safe_load(open(args.file, "r", encoding="utf-8"))
    results = [run_case(c) for c in cases]

    passed = sum(1 for r in results if r["passed"])
    total  = len(results)
    print(f"\nResults: {passed}/{total} passed\n")

    for r in results:
        mark = "✅" if r["passed"] else "❌"
        print(f"{mark} {r['id']}: text={r['ok_text']} src={r['ok_src']}")
        if not r["passed"]:
            print(f"  answer:  {r['answer']}")
            print(f"  sources: {r['sources']}")

    sys.exit(0 if passed == total else 1)

if __name__ == "__main__":
    main()
