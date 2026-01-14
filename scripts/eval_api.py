#!/usr/bin/env python3
import sys, time, argparse, requests, yaml, concurrent.futures

API_QUERY = "http://127.0.0.1:8000/query"
API_DEBUG = "http://127.0.0.1:8000/debug_query"

# FAST mode uses /debug_query and checks retrieved context instead of calling the LLM.
DEFAULT_FAST = True

TIMEOUT_QUERY = 120
TIMEOUT_DEBUG = 45

MAX_WORKERS_FAST = 8   # retrieval is cheap
MAX_WORKERS_SLOW = 2   # LLM calls queue; higher usually makes it worse

def _lower(s):
    return (s or "").lower()

def _safe_list(x):
    return x if isinstance(x, list) else []

def _expect_text_ok(case, haystack_lower: str) -> bool:
    ok_text = True
    if case.get("expect_contains"):
        ok_text = _lower(case["expect_contains"]) in haystack_lower
    if case.get("expect_contains_any"):
        opts = [_lower(s) for s in _safe_list(case["expect_contains_any"])]
        ok_text = any(opt in haystack_lower for opt in opts)
    return ok_text

def _expect_src_ok(case, sources: list[str]) -> bool:
    expects = _safe_list(case.get("expect_sources_any", []))
    if not expects:
        return True
    return any(s in sources for s in expects)

def run_case_fast(case):
    """
    FAST: call /debug_query, validate:
      - sources contain one of expect_sources_any
      - expected phrases appear in retrieved context (documents)
    """
    payload = {
        "q": case["q"],
        "topic": case.get("topic"),
        "jurisdiction": case.get("jurisdiction"),
        "k": case.get("k", 24),
    }
    try:
        r = requests.post(API_DEBUG, json=payload, timeout=TIMEOUT_DEBUG)
        r.raise_for_status()
        data = r.json() or {}
    except Exception as e:
        return {
            "id": case.get("id", "?"),
            "passed": False,
            "ok_text": False,
            "ok_src": False,
            "mode": "fast",
            "error": f"debug_query failed: {e}",
            "answer": None,
            "sources": [],
        }

    sources = _safe_list(data.get("sources", []))
    raw = data.get("raw") or {}
    docs = _safe_list(raw.get("documents", []))

    ctx = "\n\n".join(docs)
    ctx_lower = _lower(ctx)

    ok_text = _expect_text_ok(case, ctx_lower)
    ok_src = _expect_src_ok(case, sources)

    return {
        "id": case.get("id", "?"),
        "passed": ok_text and ok_src,
        "ok_text": ok_text,
        "ok_src": ok_src,
        "mode": "fast",
        "error": None,
        "answer": "(validated against retrieved context; no LLM call)",
        "sources": sources,
        "top_sources": sources[:6],
    }

def run_case_slow(case):
    """
    SLOW: call /query (LLM), validate:
      - answer contains expected phrases
      - sources contain one of expect_sources_any
    """
    payload = {
        "q": case["q"],
        "topic": case.get("topic"),
        "jurisdiction": case.get("jurisdiction"),
        "k": case.get("k", 6),
        "max_tokens": case.get("max_tokens", 96),  # lower by default to speed up
    }
    try:
        r = requests.post(API_QUERY, json=payload, timeout=TIMEOUT_QUERY)
        r.raise_for_status()
        data = r.json() or {}
    except Exception as e:
        return {
            "id": case.get("id", "?"),
            "passed": False,
            "ok_text": False,
            "ok_src": False,
            "mode": "slow",
            "error": f"query failed: {e}",
            "answer": None,
            "sources": [],
        }

    ans = _lower(data.get("answer") or "")
    sources = _safe_list(data.get("sources", []))

    ok_text = _expect_text_ok(case, ans)
    ok_src = _expect_src_ok(case, sources)

    return {
        "id": case.get("id", "?"),
        "passed": ok_text and ok_src,
        "ok_text": ok_text,
        "ok_src": ok_src,
        "mode": "slow",
        "error": None,
        "answer": data.get("answer"),
        "sources": sources,
        "top_sources": sources[:6],
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file", nargs="?", default="eval/cases.yaml")
    ap.add_argument("--slow", action="store_true", help="Use /query (LLM). Slow.")
    ap.add_argument("--workers", type=int, default=None)
    args = ap.parse_args()

    cases = yaml.safe_load(open(args.file)) or []
    if not isinstance(cases, list):
        print("cases.yaml must be a list of cases")
        sys.exit(2)

    fast = DEFAULT_FAST and not args.slow
    runner = run_case_fast if fast else run_case_slow
    workers = args.workers or (MAX_WORKERS_FAST if fast else MAX_WORKERS_SLOW)

    print(f"Running {len(cases)} evaluation cases... mode={'FAST' if fast else 'SLOW'} workers={workers}")
    start = time.time()

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as ex:
        results = list(ex.map(runner, cases))

    elapsed = time.time() - start
    passed = sum(1 for r in results if r["passed"])
    print(f"\nResults: {passed}/{len(results)} passed in {elapsed:.1f}s\n")

    for r in results:
        mark = "✅" if r["passed"] else "❌"
        print(f"{mark} {r['id']}: text={r['ok_text']} src={r['ok_src']} ({r['mode']})")
        if not r["passed"]:
            if r.get("error"):
                print(f"  error: {r['error']}")
            print(f"  top sources: {r.get('top_sources', [])}")
            if not fast:
                print(f"  answer: {r.get('answer')}")
            else:
                # In FAST mode, failures are usually retrieval misses.
                print("  note: FAST mode checks expected phrases in retrieved context, not LLM output.")
            print()

    sys.exit(0 if passed == len(results) else 1)

if __name__ == "__main__":
    main()
