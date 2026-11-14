#!/usr/bin/env python3
"""Deterministic pre-score (0-100) → runs/<id>/ranking.json (top K go to the A-H jd-evaluator).

  rank.py [--run ID] [--preset NAME]            pre-score jobs.jsonl
  rank.py select [--run ID]                      merge evals/*.json (A-H scores) → selected.json (top N)
Signals and weights come from knobs.ranking.weights; skills come from memory/resume/facts.json.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import tomllib
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts import common  # noqa: E402
from scripts import knobs as knobs_mod  # noqa: E402

TAXONOMY = common.PLUGIN / "config" / "skills-taxonomy.toml"
COMPANIES = common.PLUGIN / "config" / "companies.toml"


def load_taxonomy() -> dict[str, list[str]]:
    data = tomllib.load(open(TAXONOMY, "rb"))["skills"]
    return {v["name"]: v["aliases"] for v in data.values()}


def skills_in(text: str, tax: dict[str, list[str]]) -> set[str]:
    low = f" {text.lower()} "
    found = set()
    for name, aliases in tax.items():
        for a in aliases:
            if re.search(r"(?<![a-z0-9])" + re.escape(a.lower()) + r"(?![a-z0-9])", low):
                found.add(name)
                break
    return found


def my_skills(k: dict, tax: dict[str, list[str]]) -> set[str]:
    facts = common.read_json(common.data_root(k) / "facts.json", {}) or {}
    names = set(facts.get("skills", []))
    text = " ".join(f.get("claim", "") for f in facts.get("facts", []))
    return names | skills_in(text, tax)


def years_asked(text: str) -> int | None:
    m = re.findall(r"(\d{1,2})\s*\+?\s*(?:-|to)?\s*(?:\d{1,2}\s*)?\+?\s*years?", text.lower())
    nums = [int(x) for x in m if 0 < int(x) < 30]
    return min(nums) if nums else None


def company_tier(name: str) -> int:
    if not COMPANIES.exists():
        return 0
    for c in tomllib.load(open(COMPANIES, "rb")).get("company", []):
        if c.get("name", "").lower() == (name or "").lower():
            return int(c.get("tier", 0))
    return 0


def pre_score(j: dict, k: dict, tax: dict, mine: set[str]) -> tuple[float, dict]:
    w = k["ranking"]["weights"]
    p, s = k["profile"], k["search"]
    text = f"{j.get('title', '')}\n{j.get('description', '')}"
    parts: dict[str, float] = {}
    t = j.get("title", "").lower()
    parts["title"] = 1.0 if any(x.lower() in t for x in p["target_titles"]) else (
        0.6 if re.search(r"\b(ai|ml|llm|genai|agent)", t) else 0.0)
    asked = skills_in(text, tax)
    parts["skills"] = len(asked & mine) / max(1, len(asked)) if asked else 0.3
    ya = years_asked(text)
    parts["years"] = 0.5 if ya is None else max(0.0, 1.0 - max(0, ya - p["years_experience"]) * 0.3)
    loc = (j.get("location") or "").lower()
    loc_ok = any(x.split(",")[0].lower() in loc for x in s["locations"]) or "canada" in loc or j.get("workplace") == "remote"
    parts["fit"] = (0.6 if loc_ok else 0.2) + (0.4 if not j.get("workplace") or j["workplace"] in s["workplace"] else 0.0)
    smax = j.get("salary_max") or 0
    parts["pay"] = 0.5 if not smax else min(1.0, float(smax) / max(1, p["min_base"]))
    age = 15
    if j.get("posted_at"):
        try:
            dt = datetime.fromisoformat(j["posted_at"].replace("Z", "+00:00"))
            dt = dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
            age = (datetime.now(timezone.utc) - dt).days
        except ValueError:
            pass
    parts["fresh"] = max(0.0, 1.0 - age / max(1, k["ranking"]["fresh_days"]))
    parts["tier"] = min(1.0, company_tier(j.get("company", "")) / 3)
    score = sum(parts[x] * w[x] for x in parts) / sum(w.values()) * 100
    return round(score, 1), {"parts": {x: round(v, 2) for x, v in parts.items()}, "skills_asked": sorted(asked),
                             "skills_matched": sorted(asked & mine), "years_asked": ya}


def cmd_rank(rd: Path, k: dict) -> dict:
    tax = load_taxonomy()
    mine = my_skills(k, tax)
    jobs = list(common.read_jsonl(rd / "jobs.jsonl"))
    scored = []
    for j in jobs:
        sc, why = pre_score(j, k, tax, mine)
        scored.append({"id": j["id"], "title": j["title"], "company": j.get("company", ""), "location": j.get("location", ""),
                       "url": j["url"], "source": j.get("source"), "workplace": j.get("workplace", ""),
                       "salary": [j.get("salary_min"), j.get("salary_max"), j.get("currency", "")],
                       "pre_score": sc, **why})
    scored.sort(key=lambda x: -x["pre_score"])
    top_k = scored[: k["ranking"]["pre_rank_top_k"]]
    out = {"total": len(scored), "top_k": top_k, "rest": scored[len(top_k):]}
    common.write_json(rd / "ranking.json", out)
    return {"total": len(scored), "top_k": [{"id": x["id"], "title": x["title"], "company": x["company"], "pre_score": x["pre_score"]} for x in top_k]}


def cmd_select(rd: Path, k: dict) -> dict:
    ranking = common.read_json(rd / "ranking.json", {})
    evals = {}
    for f in (rd / "evals").glob("*.json"):
        e = common.read_json(f, {})
        if e.get("id"):
            evals[e["id"]] = e
    rows = []
    for x in ranking.get("top_k", []):
        e = evals.get(x["id"], {})
        if not e:
            continue
        rows.append({**x, "ah_score": e.get("score"), "band": e.get("band"), "why": e.get("why", ""),
                     "legitimacy": e.get("legitimacy", ""), "hard_stop": e.get("hard_stop", False)})
    rows = [r for r in rows if not r["hard_stop"] and (r["ah_score"] or 0) >= k["ranking"]["select_min"]]
    rows.sort(key=lambda r: (-(r["ah_score"] or 0), -r["pre_score"]))
    selected = rows[: k["ranking"]["select_top_n"]]
    common.write_json(rd / "selected.json", {"selected": selected, "evaluated": len(evals)})
    return {"evaluated": len(evals), "selected": len(selected)}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", nargs="?", default="rank", choices=["rank", "select"])
    ap.add_argument("--run")
    ap.add_argument("--preset")
    a = ap.parse_args(argv)
    k, _ = knobs_mod.load(a.preset)
    rd = common.run_dir(a.run, k)
    print(json.dumps(cmd_rank(rd, k) if a.cmd == "rank" else cmd_select(rd, k)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
