#!/usr/bin/env python3
"""Markdown cards for chat, built from run files (zero LLM tokens).

  cards.py tools|jobs|selected|changes|judge|result|all [--run ID] [--version N]
  cards.py --final           (Stop hook) print all cards once when a run finished and not yet shown
Cards:
  1 tools     tool/source calls ok/failed + reasons + cost   (ledger.jsonl)
  2 jobs      found per source → unique → filtered → live → pre-ranked (funnel.json, ranking.json)
  3 selected  only the selected jobs, in detail            (selected.json)
  4 changes   what / why changed in v{n}                     (versions/v{n}/changes.json)
  5 judge     blind judge verdict for v{n}                   (versions/v{n}/judge.json)
  6 result    link to resume-v{n}.pdf + score history
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts import common  # noqa: E402
from scripts import knobs as knobs_mod  # noqa: E402
from scripts import ledger as ledger_mod  # noqa: E402


def _esc(s: object, n: int = 60) -> str:
    t = str(s if s is not None else "").replace("|", "/").replace("\n", " ")
    return t if len(t) <= n else t[: n - 1] + "…"


def card_tools(rd: Path) -> str:
    s = ledger_mod.summary(rd.name)
    rows = ["### 🔧 Card 1 — Tools", "", "| Tool / source | Calls | OK | Failed | Fail reasons |", "|---|---:|---:|---:|---|"]
    groups: dict[str, dict] = {}
    for src, v in s["by_source"].items():
        key = src.split(":")[0] + (":" + src.split(":")[1] if src.startswith("scanner:") else "")
        g = groups.setdefault(key, {"calls": 0, "ok": 0, "failed": 0, "reasons": {}})
        for f in ("calls", "ok", "failed"):
            g[f] += v[f]
        for r, c in v["reasons"].items():
            g["reasons"][r] = g["reasons"].get(r, 0) + c
    for k, v in sorted(groups.items(), key=lambda kv: -kv[1]["calls"])[:40]:
        reasons = ", ".join(f"{r} ×{c}" for r, c in v["reasons"].items()) or "—"
        rows.append(f"| {_esc(k, 45)} | {v['calls']} | {v['ok']} | {v['failed']} | {_esc(reasons, 70)} |")
    t = s["total"]
    rows.append(f"| **Total** | **{t['calls']}** | **{t['ok']}** | **{t['failed']}** | cost ${t['cost']} |")
    return "\n".join(rows)


def card_jobs(rd: Path) -> str:
    f = common.read_json(rd / "funnel.json", {}) or {}
    r = common.read_json(rd / "ranking.json", {}) or {}
    lv = f.get("liveness", {})
    rows = ["### 📥 Card 2 — Jobs found", "",
            f"**{f.get('found', 0)}** found → **{f.get('unique', 0)}** unique → **{f.get('after_filters', 0)}** after knob filters → "
            f"**{f.get('kept', 0)}** live (dead {lv.get('dead', 0)}, unknown {lv.get('unknown', 0)}) → "
            f"**{len(r.get('top_k', []))}** pre-ranked for A–H", ""]
    if f.get("dropped"):
        rows.append("Dropped: " + ", ".join(f"{k} {v}" for k, v in f["dropped"].items()))
        rows.append("")
    rows += ["| Source | Jobs |", "|---|---:|"]
    for src, n in sorted((f.get("by_source") or {}).items(), key=lambda kv: -kv[1])[:25]:
        rows.append(f"| {_esc(src, 40)} | {n} |")
    return "\n".join(rows)


def card_selected(rd: Path) -> str:
    sel = (common.read_json(rd / "selected.json", {}) or {}).get("selected", [])
    rows = [f"### 🎯 Card 3 — Selected jobs ({len(sel)})", "",
            "| # | Role | Company | Where | Pay | A–H | Pre | Why |", "|---:|---|---|---|---|---:|---:|---|"]
    for i, s in enumerate(sel, 1):
        lo, hi, cur = (s.get("salary") or [None, None, ""]) + [None] * 0
        pay = f"{cur} {int(lo or 0):,}–{int(hi or 0):,}" if hi else "—"
        where = f"{s.get('location', '')} {('· ' + s['workplace']) if s.get('workplace') else ''}"
        rows.append(f"| {i} | [{_esc(s['title'], 40)}]({s['url']}) | {_esc(s['company'], 25)} | {_esc(where, 30)} | {pay} | "
                    f"{s.get('ah_score', '—')} | {s.get('pre_score', '—')} | {_esc(s.get('why', ''), 80)} |")
    return "\n".join(rows)


def _version_dir(k: dict, n: int | None) -> Path | None:
    vroot = common.data_root(k) / "versions"
    if not vroot.exists():
        return None
    vs = sorted((int(p.name[1:]), p) for p in vroot.glob("v*") if p.name[1:].isdigit())
    if not vs:
        return None
    if n is None:
        return vs[-1][1]
    return next((p for i, p in vs if i == n), None)


def card_changes(k: dict, n: int | None) -> str:
    vd = _version_dir(k, n)
    if not vd:
        return "### ✍️ Card 4 — Changes\n\n(no version yet)"
    ch = common.read_json(vd / "changes.json", {}) or {}
    rows = [f"### ✍️ Card 4 — {vd.name} changes (parent {ch.get('parent', '—')})", "",
            "| # | Section | Before → After | Why | Job words | Facts |", "|---:|---|---|---|---|---|"]
    for i, c in enumerate(ch.get("changes", []), 1):
        rows.append(f"| {i} | {_esc(c.get('section'), 20)} | {_esc(c.get('before'), 45)} → **{_esc(c.get('after'), 55)}** | "
                    f"{_esc(c.get('why'), 50)} | {_esc(', '.join(c.get('job_words', [])), 35)} | {_esc(', '.join(c.get('fact_ids', [])), 20)} |")
    sc = common.read_json(vd / "scores.json", {}) or {}
    if sc:
        rows += ["", f"Gates: fact `{sc.get('fact_gate', '—')}` · lint `{sc.get('lint', '—')}` · ATS `{sc.get('ats', '—')}` · "
                     f"keyword coverage {sc.get('keyword_coverage', '—')} · pages {sc.get('pages', '—')}"]
    return "\n".join(rows)


def card_judge(k: dict, n: int | None) -> str:
    vd = _version_dir(k, n)
    j = common.read_json(vd / "judge.json", {}) if vd else {}
    if not j:
        return "### ⚖️ Card 5 — Judge\n\n(not judged yet)"
    rows = [f"### ⚖️ Card 5 — Blind judge on {vd.name}: **{j.get('score')} / 10** → **{j.get('verdict', '?')}**", "",
            f"Round job: {_esc(j.get('job_title'), 50)} @ {_esc(j.get('job_company'), 30)}"
            + (f" · holdout: {j.get('holdout_score')} on {_esc(j.get('holdout_title'), 40)}" if j.get("holdout_score") is not None else ""), "",
            "| Criterion | Score |", "|---|---:|"]
    for c, v in (j.get("criteria") or {}).items():
        rows.append(f"| {_esc(c, 40)} | {v} |")
    if j.get("reasons"):
        rows += ["", "**Reasons:** " + " · ".join(_esc(r, 120) for r in j["reasons"])]
    if j.get("fixes"):
        rows += ["", "**Fixes asked:** " + " · ".join(_esc(r, 120) for r in j["fixes"])]
    return "\n".join(rows)


def card_result(k: dict) -> str:
    vroot = common.data_root(k) / "versions"
    hist = []
    for p in sorted(vroot.glob("v*"), key=lambda p: int(p.name[1:]) if p.name[1:].isdigit() else 0):
        j = common.read_json(p / "judge.json", {}) or {}
        sc = common.read_json(p / "scores.json", {}) or {}
        hist.append((p.name, j.get("score"), sc.get("keyword_coverage")))
    vd = _version_dir(k, None)
    if not vd:
        return "### 🏁 Card 6 — Result\n\n(no versions)"
    pdf = vd / f"resume-{vd.name}.pdf"
    rel = pdf.relative_to(common.repo_root()) if pdf.is_relative_to(common.repo_root()) else pdf
    rows = ["### 🏁 Card 6 — Result", "", f"**New resume:** [`{rel}`]({rel})" + ("" if pdf.exists() else " (PDF not built — run build.sh)"), "",
            "| Version | Judge | Keyword coverage |", "|---|---:|---:|"]
    rows += [f"| {v} | {s if s is not None else '—'} | {c if c is not None else '—'} |" for v, s, c in hist]
    return "\n".join(rows)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("card", nargs="?", default="all", choices=["tools", "jobs", "selected", "changes", "judge", "result", "all"])
    ap.add_argument("--run")
    ap.add_argument("--version", type=int)
    ap.add_argument("--final", action="store_true")
    a = ap.parse_args(argv)
    k, _ = knobs_mod.load()
    if a.final:
        try:
            rd = common.run_dir(a.run, k)
        except SystemExit:
            return 0
        done, shown = rd / "DONE", rd / "CARDS_SHOWN"
        if not done.exists() or shown.exists():
            return 0
        shown.write_text("1")
        text = "\n\n".join([card_tools(rd), card_jobs(rd), card_selected(rd), card_changes(k, None), card_judge(k, None), card_result(k)])
        print(json.dumps({"systemMessage": text}))
        return 0
    rd = common.run_dir(a.run, k) if a.card in ("tools", "jobs", "selected", "all") else None
    out = {
        "tools": lambda: card_tools(rd), "jobs": lambda: card_jobs(rd), "selected": lambda: card_selected(rd),
        "changes": lambda: card_changes(k, a.version), "judge": lambda: card_judge(k, a.version), "result": lambda: card_result(k),
        "all": lambda: "\n\n".join([card_tools(rd), card_jobs(rd), card_selected(rd), card_changes(k, a.version),
                                    card_judge(k, a.version), card_result(k)]),
    }[a.card]()
    (rd / "cards.md").write_text(out, encoding="utf-8") if rd and a.card == "all" else None
    print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
