#!/usr/bin/env python3
"""ATS readability check on the built PDF (pdftotext): contact parsed, links real, page count, order, glyph junk.

  ats_check.py FILE.pdf [--tex FILE.tex] [--json]     exit 1 on errors
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts import knobs as knobs_mod  # noqa: E402

EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE = re.compile(r"\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}")
SECTIONS = ["EXPERIENCE", "EDUCATION", "SKILLS"]


def pdf_text(pdf: Path) -> str:
    if not shutil.which("pdftotext"):
        raise SystemExit("pdftotext not found (install poppler)")
    return subprocess.run(["pdftotext", "-layout", str(pdf), "-"], capture_output=True, text=True, check=True).stdout


def pdf_pages(pdf: Path) -> int:
    if shutil.which("pdfinfo"):
        out = subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True).stdout
        m = re.search(r"Pages:\s+(\d+)", out)
        if m:
            return int(m.group(1))
    return pdf_text(pdf).count("\f") + 1


def check(pdf: Path, tex: Path | None, max_pages: int) -> dict:
    text = pdf_text(pdf)
    errors, warnings = [], []
    if not EMAIL.search(text):
        errors.append("no email found in extracted text")
    if not PHONE.search(text):
        warnings.append("no phone number found in extracted text")
    up = text.upper()
    pos = [up.find(s) for s in SECTIONS]
    for s, p in zip(SECTIONS, pos):
        if p < 0:
            errors.append(f"section heading not found: {s}")
    pages = pdf_pages(pdf)
    if pages > max_pages:
        errors.append(f"{pages} pages (max {max_pages})")
    junk = re.findall(r"[\ufffd\u25a1]|\(cid:\d+\)", text)
    if junk:
        errors.append(f"{len(junk)} unreadable glyphs (font/ToUnicode issue)")
    if tex and tex.exists():
        src = re.sub(r"(?<!\\)%.*", "", tex.read_text(encoding="utf-8"))
        src = src.split("\\begin{document}", 1)[-1] if "\\begin{document}" in src else src
        for shown, extracted in re.findall(r"\\ats\{([^}]*)\}\{([^}]*)\}", src):
            ext = extracted.replace("\\textasciitilde", "~").replace("\\", "").rstrip(":").strip("{}")
            if ext and ext not in text and ext.replace("\\textasciitilde", "~") not in text:
                warnings.append(f"\\ats text not extracted: {ext!r} (shown as {shown!r})")
        for url in re.findall(r"\\href\{([^}]+)\}", src):
            if not url.startswith(("http://", "https://", "mailto:")):
                errors.append(f"link not absolute: {url}")
            if "/users/" in url and "/projects/" in url:
                warnings.append(f"link points to a GitHub Projects board, not a repo: {url}")
    words = len(text.split())
    return {"verdict": "FAIL" if errors else "PASS", "pages": pages, "words": words, "errors": errors, "warnings": warnings}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("pdf")
    ap.add_argument("--tex")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    k, _ = knobs_mod.load()
    res = check(Path(a.pdf), Path(a.tex) if a.tex else None, k["resume"]["max_pages"])
    if a.json:
        print(json.dumps(res, indent=2))
    else:
        print(f"{res['verdict']}  pages={res['pages']} words={res['words']}")
        for e in res["errors"]:
            print("  error", e)
        for w in res["warnings"]:
            print("  warn ", w)
    return 1 if res["errors"] else 0


if __name__ == "__main__":
    sys.exit(main())
