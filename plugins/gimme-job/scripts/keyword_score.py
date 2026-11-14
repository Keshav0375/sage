#!/usr/bin/env python3
"""Keyword coverage: skills the selected jobs ask for vs skills in the resume text.

  keyword_score.py RESUME(.pdf|.tex) [--run ID] [--job ID] [--json]
Coverage = share of asked skills (weighted by how many selected jobs ask) that appear in the resume.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts import common  # noqa: E402
from scripts import knobs as knobs_mod  # noqa: E402
from scripts.facts import tex_text  # noqa: E402
from scripts.rank import load_taxonomy, skills_in  # noqa: E402


def resume_text(path: Path) -> str:
    if path.suffix == ".pdf":
        from scripts.ats_check import pdf_text
        return pdf_text(path)
    return tex_text(path.read_text(encoding="utf-8"))


def score(resume: str, jobs: list[dict]) -> dict:
    tax = load_taxonomy()
    have = skills_in(resume, tax)
    asked = Counter()
    for j in jobs:
        asked.update(skills_in(f"{j.get('title', '')}\n{j.get('description', '')}", tax))
    total = sum(asked.values()) or 1
    hit = sum(c for s, c in asked.items() if s in have)
    missing = [(s, c) for s, c in asked.most_common() if s not in have]
    return {"coverage": round(hit / total, 3), "asked": dict(asked.most_common()), "missing": [s for s, _ in missing],
            "missing_weighted": dict(missing), "jobs": len(jobs)}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("resume")
    ap.add_argument("--run")
    ap.add_argument("--job")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    k, _ = knobs_mod.load()
    rd = common.run_dir(a.run, k)
    by_id = {j["id"]: j for j in common.read_jsonl(rd / "jobs.jsonl")}
    sel = [s["id"] for s in (common.read_json(rd / "selected.json", {}) or {}).get("selected", [])]
    ids = [a.job] if a.job else sel
    jobs = [by_id[i] for i in ids if i in by_id]
    res = score(resume_text(Path(a.resume)), jobs)
    if a.json:
        print(json.dumps(res, indent=2))
    else:
        print(f"coverage {res['coverage']:.0%} over {res['jobs']} jobs; missing: {', '.join(res['missing'][:12]) or 'none'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
