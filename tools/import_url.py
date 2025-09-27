#!/usr/bin/env python3
import argparse, os, subprocess, tempfile, pathlib, requests, sys

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123 Safari/537.36"

def fetch(url: str, out_bin: str):
    # Try requests first
    try:
        r = requests.get(url, headers={"User-Agent": UA}, timeout=60)
        r.raise_for_status()
        open(out_bin, "wb").write(r.content)
        return
    except Exception as e:
        # Fallback to curl (often handles finicky TLS better)
        try:
            subprocess.check_call(["curl", "-fsSL", "-A", UA, "-o", out_bin, url])
            return
        except Exception:
            raise RuntimeError(f"download failed: {e}")

def html_to_md(html_path: str) -> str:
    # prefer pandoc
    try:
        return subprocess.check_output(
            ["pandoc", "-f", "html", "-t", "gfm", html_path],
            text=True
        )
    except Exception:
        # fallback lynx -> plain text
        try:
            return subprocess.check_output(
                ["lynx", "-dump", "-nolist", f"file://{html_path}"],
                text=True
            )
        except Exception as e:
            raise RuntimeError(f"html convert failed: {e}")

def pdf_to_text(pdf_path: str) -> str:
    return subprocess.check_output(["pdftotext", "-layout", pdf_path, "-"], text=True)

def write_frontmatter(source_url_or_path: str, topic: str) -> str:
    return f"""---
title: ""
jurisdiction: "TN"
topic: "{topic}"
source_url: "{source_url_or_path}"
citation: ""
doc_id: ""
accessed: ""
version_date: ""
---

"""

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out", help="Output markdown file (e.g., docs/tn/sunshine/foo.md)")
    ap.add_argument("--topic", default="sunshine", help="Frontmatter topic")
    ap.add_argument("--url", help="Fetch from URL (html/pdf)")
    ap.add_argument("--from-file", help="Ingest from local file (html/pdf)")
    args = ap.parse_args()

    if not args.url and not args.from_file:
        print("error: either --url or --from-file is required", file=sys.stderr)
        sys.exit(2)

    out = args.out
    pathlib.Path(out).parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as td:
        binpath = os.path.join(td, "src.bin")
        src_label = args.url or args.from_file

        if args.url:
            fetch(args.url, binpath)
        else:
            open(binpath, "wb").write(open(args.from_file, "rb").read())

        # detect file type by header/extension
        with open(binpath, "rb") as fh:
            head = fh.read(5)

        is_pdf = (
            (args.url and args.url.lower().endswith(".pdf")) or
            (args.from_file and args.from_file.lower().endswith(".pdf")) or
            head == b"%PDF-"
        )

        if is_pdf:
            body = pdf_to_text(binpath)
        else:
            html = binpath + ".html"
            os.replace(binpath, html)
            body = html_to_md(html)

    pathlib.Path(out).write_text(write_frontmatter(src_label, args.topic) + body, encoding="utf-8")
    print(f"[ok] wrote {out}")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
import argparse, os, subprocess, tempfile, pathlib, requests, sys

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123 Safari/537.36"

def fetch(url: str, out_bin: str):
    # Try requests first
    try:
        r = requests.get(url, headers={"User-Agent": UA}, timeout=60)
        r.raise_for_status()
        open(out_bin, "wb").write(r.content)
        return
    except Exception as e:
        # Fallback to curl (often handles finicky TLS better)
        try:
            subprocess.check_call(["curl", "-fsSL", "-A", UA, "-o", out_bin, url])
            return
        except Exception:
            raise RuntimeError(f"download failed: {e}")

def html_to_md(html_path: str) -> str:
    # prefer pandoc
    try:
        return subprocess.check_output(
            ["pandoc", "-f", "html", "-t", "gfm", html_path],
            text=True
        )
    except Exception:
        # fallback lynx -> plain text
        try:
            return subprocess.check_output(
                ["lynx", "-dump", "-nolist", f"file://{html_path}"],
                text=True
            )
        except Exception as e:
            raise RuntimeError(f"html convert failed: {e}")

def pdf_to_text(pdf_path: str) -> str:
    return subprocess.check_output(["pdftotext", "-layout", pdf_path, "-"], text=True)

def write_frontmatter(source_url_or_path: str, topic: str) -> str:
    return f"""---
title: ""
jurisdiction: "TN"
topic: "{topic}"
source_url: "{source_url_or_path}"
citation: ""
doc_id: ""
accessed: ""
version_date: ""
---

"""

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out", help="Output markdown file (e.g., docs/tn/sunshine/foo.md)")
    ap.add_argument("--topic", default="sunshine", help="Frontmatter topic")
    ap.add_argument("--url", help="Fetch from URL (html/pdf)")
    ap.add_argument("--from-file", help="Ingest from local file (html/pdf)")
    args = ap.parse_args()

    if not args.url and not args.from_file:
        print("error: either --url or --from-file is required", file=sys.stderr)
        sys.exit(2)

    out = args.out
    pathlib.Path(out).parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as td:
        binpath = os.path.join(td, "src.bin")
        src_label = args.url or args.from_file

        if args.url:
            fetch(args.url, binpath)
        else:
            open(binpath, "wb").write(open(args.from_file, "rb").read())

        # detect file type by header/extension
        with open(binpath, "rb") as fh:
            head = fh.read(5)

        is_pdf = (
            (args.url and args.url.lower().endswith(".pdf")) or
            (args.from_file and args.from_file.lower().endswith(".pdf")) or
            head == b"%PDF-"
        )

        if is_pdf:
            body = pdf_to_text(binpath)
        else:
            html = binpath + ".html"
            os.replace(binpath, html)
            body = html_to_md(html)

    pathlib.Path(out).write_text(write_frontmatter(src_label, args.topic) + body, encoding="utf-8")
    print(f"[ok] wrote {out}")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
import argparse, os, subprocess, tempfile, pathlib, requests, sys

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123 Safari/537.36"

def fetch(url: str, out_bin: str):
    # Try requests first
    try:
        r = requests.get(url, headers={"User-Agent": UA}, timeout=60)
        r.raise_for_status()
        open(out_bin, "wb").write(r.content)
        return
    except Exception as e:
        # Fallback to curl (often handles finicky TLS better)
        try:
            subprocess.check_call(["curl", "-fsSL", "-A", UA, "-o", out_bin, url])
            return
        except Exception:
            raise RuntimeError(f"download failed: {e}")

def html_to_md(html_path: str) -> str:
    # prefer pandoc
    try:
        return subprocess.check_output(
            ["pandoc", "-f", "html", "-t", "gfm", html_path],
            text=True
        )
    except Exception:
        # fallback lynx -> plain text
        try:
            return subprocess.check_output(
                ["lynx", "-dump", "-nolist", f"file://{html_path}"],
                text=True
            )
        except Exception as e:
            raise RuntimeError(f"html convert failed: {e}")

def pdf_to_text(pdf_path: str) -> str:
    return subprocess.check_output(["pdftotext", "-layout", pdf_path, "-"], text=True)

def write_frontmatter(source_url_or_path: str, topic: str) -> str:
    return f"""---
title: ""
jurisdiction: "TN"
topic: "{topic}"
source_url: "{source_url_or_path}"
citation: ""
doc_id: ""
accessed: ""
version_date: ""
---

"""

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out", help="Output markdown file (e.g., docs/tn/sunshine/foo.md)")
    ap.add_argument("--topic", default="sunshine", help="Frontmatter topic")
    ap.add_argument("--url", help="Fetch from URL (html/pdf)")
    ap.add_argument("--from-file", help="Ingest from local file (html/pdf)")
    args = ap.parse_args()

    if not args.url and not args.from_file:
        print("error: either --url or --from-file is required", file=sys.stderr)
        sys.exit(2)

    out = args.out
    pathlib.Path(out).parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as td:
        binpath = os.path.join(td, "src.bin")
        src_label = args.url or args.from_file

        if args.url:
            fetch(args.url, binpath)
        else:
            open(binpath, "wb").write(open(args.from_file, "rb").read())

        # detect file type
        with open(binpath, "rb") as fh:
            head = fh.read(5)

        if (args.url and args.url.lower().endswith(".pdf")) \
           or (args.from_file and args.from_file.lower().endswith(".pdf")) \
           or head == b"%PDF-":
            body = pdf_to_text(binpath)
        else:
            html = binpath + ".html"
            os.replace(binpath, html)
            body = html_to_md(html)

    pathlib.Path(out).write_text(write_frontmatter(src_label, args.topic) + body, encoding="utf-8")
    print(f"[ok] wrote {out}")

if __name__ == "__main__":
    main()
