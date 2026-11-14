#!/usr/bin/env python3
"""Resume versions: memory/resume/versions/v{n}/ with resume-v{n}.tex|.pdf, changes.md|json, scores.json, judge.json.

  version.py new [--from N] [--run ID]     copy v{N or latest} → v{latest+1}; write changes skeleton
  version.py list
  version.py latest                        print latest version number
  version.py diff A B                      unified diff of resume-vA.tex vs resume-vB.tex
  version.py render N                      changes.json → changes.md
  version.py best                          version with the highest judge score
"""
from __future__ import annotations

import argparse
import difflib
import json
import shutil
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts import common  # noqa: E402
from scripts import knobs as knobs_mod  # noqa: E402


def vroot(k: dict) -> Path:
    return common.data_root(k) / "versions"


def versions(k: dict) -> list[int]:
    r = vroot(k)
    return sorted(int(p.name[1:]) for p in r.glob("v*") if p.is_dir() and p.name[1:].isdigit()) if r.exists() else []


def vdir(k: dict, n: int) -> Path:
    return vroot(k) / f"v{n}"


def tex_path(k: dict, n: int) -> Path:
    return vdir(k, n) / f"resume-v{n}.tex"


def new_version(k: dict, src: int | None = None, run: str | None = None) -> int:
    vs = versions(k)
    if not vs:
        raise SystemExit("no v1 yet: import the current resume as versions/v1/resume-v1.tex first")
    src = src or vs[-1]
    n = vs[-1] + 1
    d = vdir(k, n)
    d.mkdir(parents=True)
    shutil.copy(tex_path(k, src), tex_path(k, n))
    meta = {"version": f"v{n}", "parent": f"v{src}", "date": time.strftime("%Y-%m-%d"), "run": run or "",
            "why": "", "judge_reasons_addressed": [], "changes": [], "locked_facts_kept": True,
            "jobs_used": {"selected": [], "round_job": "", "holdout_job": ""}}
    common.write_json(d / "changes.json", meta)
    (d / "changes.md").write_text(render(meta, {}, {}), encoding="utf-8")
    return n


def render(meta: dict, scores: dict, judge: dict) -> str:
    L = [f"# {meta['version']} — {meta.get('date', '')} — run {meta.get('run') or '—'} — parent {meta.get('parent', '—')}", "",
         "## Why this version", "", meta.get("why") or "_(filled by writer-lead)_", ""]
    if meta.get("judge_reasons_addressed"):
        L += ["Judge reasons addressed:", *[f"- {r}" for r in meta["judge_reasons_addressed"]], ""]
    L += ["## Changes", "", "| # | Section | Before | After | Why | Job words | Fact ids | Sources |", "|---|---|---|---|---|---|---|---|"]
    for i, c in enumerate(meta.get("changes", []), 1):
        cell = lambda s: str(s or "").replace("|", "/").replace("\n", " ")  # noqa: E731
        L.append(f"| {i} | {cell(c.get('section'))} | {cell(c.get('before'))} | {cell(c.get('after'))} | {cell(c.get('why'))} | "
                 f"{cell(', '.join(c.get('job_words', [])))} | {cell(', '.join(c.get('fact_ids', [])))} | {cell(', '.join(c.get('sources', [])))} |")
    L += ["", "## Locked facts kept", "", "Titles, employers, dates and every number are unchanged unless a fact id says otherwise."
          if meta.get("locked_facts_kept", True) else "**WARNING: locked facts changed — see fact gate.**", ""]
    if scores:
        L += ["## Scores", "", "| Gate | Result |", "|---|---|"] + [f"| {k} | {v} |" for k, v in scores.items()] + [""]
    if judge:
        L += ["## Blind judge", "", f"Score **{judge.get('score')}** / 10 → {judge.get('verdict')} "
              f"(round job: {judge.get('job_title', '')} @ {judge.get('job_company', '')})", ""]
        L += [f"- {r}" for r in judge.get("reasons", [])] + [""]
    ju = meta.get("jobs_used", {})
    L += ["## Jobs used", "", f"- Selected: {', '.join(ju.get('selected', [])) or '—'}",
          f"- Round job: {ju.get('round_job') or '—'}", f"- Holdout job: {ju.get('holdout_job') or '—'}", ""]
    return "\n".join(L)


def render_version(k: dict, n: int) -> Path:
    d = vdir(k, n)
    meta = common.read_json(d / "changes.json", {}) or {"version": f"v{n}"}
    md = render(meta, common.read_json(d / "scores.json", {}) or {}, common.read_json(d / "judge.json", {}) or {})
    (d / "changes.md").write_text(md, encoding="utf-8")
    return d / "changes.md"


def best(k: dict) -> tuple[int, float | None]:
    top = (versions(k)[-1] if versions(k) else 0, None)
    for n in versions(k):
        s = (common.read_json(vdir(k, n) / "judge.json", {}) or {}).get("score")
        if s is not None and (top[1] is None or s > top[1]):
            top = (n, s)
    return top


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["new", "list", "latest", "diff", "render", "best"])
    ap.add_argument("args", nargs="*")
    ap.add_argument("--from", dest="src", type=int)
    ap.add_argument("--run")
    a = ap.parse_args(argv)
    k, _ = knobs_mod.load()
    if a.cmd == "new":
        n = new_version(k, a.src, a.run)
        print(json.dumps({"version": n, "tex": str(tex_path(k, n))}))
    elif a.cmd == "list":
        for n in versions(k):
            j = common.read_json(vdir(k, n) / "judge.json", {}) or {}
            print(f"v{n}  judge={j.get('score', '—')}  {j.get('verdict', '')}")
    elif a.cmd == "latest":
        print(versions(k)[-1] if versions(k) else 0)
    elif a.cmd == "diff":
        x, y = int(a.args[0]), int(a.args[1])
        sys.stdout.writelines(difflib.unified_diff(tex_path(k, x).read_text().splitlines(True), tex_path(k, y).read_text().splitlines(True),
                                                   f"resume-v{x}.tex", f"resume-v{y}.tex"))
    elif a.cmd == "render":
        print(render_version(k, int(a.args[0])))
    elif a.cmd == "best":
        n, s = best(k)
        print(json.dumps({"version": n, "score": s}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
