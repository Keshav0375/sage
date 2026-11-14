#!/usr/bin/env python3
"""Setup check: binaries, scanner registry, knobs, data folder, gitignore rules. Exit 1 if a must-have fails."""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts import common  # noqa: E402
from scripts import knobs as knobs_mod  # noqa: E402
from scripts.providers import _registry  # noqa: E402

EXPECTED_SCANNERS = 145


def main() -> int:
    rows: list[tuple[str, bool, str, bool]] = []  # (check, ok, detail, must)
    rows.append(("python >= 3.11", sys.version_info >= (3, 11), sys.version.split()[0], True))
    tect = shutil.which("tectonic") or shutil.which("latexmk") or shutil.which("pdflatex")
    rows.append(("LaTeX engine (tectonic)", bool(tect), tect or "brew install tectonic", True))
    rows.append(("pdftotext (poppler)", bool(shutil.which("pdftotext")), shutil.which("pdftotext") or "brew install poppler", True))
    n = len(_registry.all_providers())
    rows.append((f"scanners registered = {EXPECTED_SCANNERS}", n == EXPECTED_SCANNERS, str(n), True))
    try:
        k, _ = knobs_mod.load()
        rows.append(("knobs valid", True, str(knobs_mod.user_file()), True))
    except SystemExit as e:
        k = {}
        rows.append(("knobs valid", False, str(e), True))
    dr = common.data_root(k)
    v1 = dr / "versions" / "v1" / "resume-v1.tex"
    rows.append(("data root", dr.exists(), str(dr), True))
    rows.append(("resume v1 imported", v1.exists(), str(v1), False))
    rows.append(("facts.json", (dr / "facts.json").exists(), str(dr / "facts.json"), False))
    rows.append(("contact.tex (private)", (dr / "contact.tex").exists(), str(dr / "contact.tex"), False))
    for probe in ("memory/resume/contact.tex", "memory/resume/versions/v1/resume-v1.pdf", "memory/resume/runs/x/ledger.jsonl"):
        r = subprocess.run(["git", "check-ignore", "-q", probe], cwd=common.repo_root())
        rows.append((f"gitignored: {probe}", r.returncode == 0, "ok" if r.returncode == 0 else "add rule to .gitignore", True))
    width = max(len(r[0]) for r in rows)
    bad = False
    for name, ok, detail, must in rows:
        mark = "ok  " if ok else ("FAIL" if must else "warn")
        bad |= (not ok and must)
        print(f"{mark}  {name:<{width}}  {detail}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
