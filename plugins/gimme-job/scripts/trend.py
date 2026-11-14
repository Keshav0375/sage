#!/usr/bin/env python3
"""Market snapshot: skill frequency, years asked, pay, top companies → market/snapshots/<date>.md (+ delta).

  trend.py [--run ID] [--preset NAME]
Only aggregate counts are written (safe to commit). Raw job text stays in the gitignored run folder.
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts import common  # noqa: E402
from scripts import knobs as knobs_mod  # noqa: E402
from scripts.rank import load_taxonomy, skills_in, years_asked  # noqa: E402


def snapshot(jobs: list[dict]) -> dict:
    tax = load_taxonomy()
    with_text = [j for j in jobs if j.get("description")]
    skill = Counter()
    for j in with_text:
        skill.update(skills_in(j["description"], tax))
    years = [y for y in (years_asked(j["description"]) for j in with_text) if y is not None]
    pay = [float(j["salary_max"]) for j in jobs if j.get("salary_max") and (j.get("salary_period") in ("", "year", None))]
    return {
        "date": time.strftime("%Y-%m-%d"), "jobs": len(jobs), "with_text": len(with_text),
        "skills": dict(skill.most_common(40)),
        "years_median": statistics.median(years) if years else None,
        "years_3plus_share": round(sum(1 for y in years if y >= 3) / len(years), 2) if years else None,
        "pay_max_median": statistics.median(pay) if pay else None,
        "top_companies": dict(Counter(j.get("company", "") for j in jobs if j.get("company")).most_common(15)),
        "workplace": dict(Counter(j.get("workplace") or "unknown" for j in jobs)),
        "sources": dict(Counter(j.get("source", "?") for j in jobs)),
    }


def render(s: dict, prev: dict | None) -> str:
    n = max(1, s["with_text"])
    pn = max(1, (prev or {}).get("with_text", 1))
    lines = [f"# Market snapshot — {s['date']}", "",
             f"Jobs: {s['jobs']} (with text: {s['with_text']}) · median years asked: {s['years_median']} · "
             f"3+ yrs share: {s['years_3plus_share']} · median max pay: {s['pay_max_median']}", "",
             "| Skill | Jobs | Share | Δ vs last |", "|---|---|---|---|"]
    for name, c in s["skills"].items():
        share = c / n
        delta = ""
        if prev and name in prev.get("skills", {}):
            d = share - prev["skills"][name] / pn
            delta = f"{d:+.0%}"
        elif prev:
            delta = "new"
        lines.append(f"| {name} | {c} | {share:.0%} | {delta} |")
    lines += ["", "| Company | Jobs |", "|---|---|"] + [f"| {c} | {v} |" for c, v in s["top_companies"].items()]
    lines += ["", f"Workplace: {s['workplace']}", f"Sources: {s['sources']}", ""]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run")
    ap.add_argument("--preset")
    a = ap.parse_args(argv)
    k, _ = knobs_mod.load(a.preset)
    rd = common.run_dir(a.run, k)
    jobs = list(common.read_jsonl(rd / "jobs.jsonl")) or list(common.read_jsonl(rd / "jobs.raw.jsonl"))
    s = snapshot(jobs)
    snap_dir = common.data_root(k) / "market" / "snapshots"
    snap_dir.mkdir(parents=True, exist_ok=True)
    prev_files = sorted(p for p in snap_dir.glob("*.json") if p.stem != s["date"])
    prev = common.read_json(prev_files[-1]) if prev_files else None
    common.write_json(snap_dir / f"{s['date']}.json", s)
    (snap_dir / f"{s['date']}.md").write_text(render(s, prev), encoding="utf-8")
    print(json.dumps({"snapshot": str(snap_dir / f"{s['date']}.md"), "jobs": s["jobs"], "top": list(s["skills"])[:8]}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
