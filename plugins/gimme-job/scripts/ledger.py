#!/usr/bin/env python3
"""Run ledger: every tool call (ok / failed + reason), budget guard, report-file guard, tier guard.

Hook modes read the hook JSON event on stdin (Claude Code hooks contract) and print a decision.
  ledger.py --record          PostToolUse: append {tool, status, reason} to runs/<id>/ledger.jsonl
  ledger.py --budget-check    PreToolUse (mcp__composio__*): deny when the run's call cap is hit
  ledger.py --tier-check      PreToolUse (Agent): deny spawning a gimme-job agent whose model breaks the tier table
  ledger.py --report-check    SubagentStop: warn when a gimme-job worker wrote no report file
CLI:
  ledger.py summary [--run ID] [--json]
  ledger.py add --tool NAME --status ok|failed|blocked [--reason TEXT] [--source NAME] [--cost USD]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts import common  # noqa: E402
from scripts import knobs as knobs_mod  # noqa: E402

COMPOSIO_PRICE = 0.0002          # USD per call seen on 2026-11-14 (instant account, LinkedIn)

TIERS = {                        # agent name → required model tier
    "scout-lead": "coordinator", "analyst-lead": "coordinator", "writer-lead": "coordinator",
    "source-worker": "worker", "signal-worker": "worker", "mail-worker": "worker", "page-worker": "worker",
    "extract-worker": "worker", "evidence-worker": "worker", "script-worker": "worker",
    "jd-evaluator": "reasoner", "gap-analyst": "reasoner", "resume-writer": "reasoner", "fact-checker": "reasoner",
    "blind-judge": "judge",
}


def _ledger_path(run: str | None = None) -> Path | None:
    try:
        return common.run_dir(run) / "ledger.jsonl"
    except SystemExit:
        return None


def _classify(resp: object) -> tuple[str, str]:
    """Map a tool_response to (status, reason)."""
    text = json.dumps(resp)[:4000] if not isinstance(resp, str) else resp[:4000]
    low = text.lower()
    if re.search(r'"is_error"\s*:\s*true|"successful"\s*:\s*false|"error"\s*:\s*"[^"]+"|traceback|exit code [1-9]', low):
        for pat, why in [(r"429|rate limit|high usage", "429 rate limit"), (r"out of credits|wallet", "out of credits"),
                         (r"enotfound|not resolve|blocked|403", "blocked host"), (r"timeout|timed out", "timeout"),
                         (r"404|not found", "404 not found"), (r"401|unauthori", "auth")]:
            if re.search(pat, low):
                return "failed", why
        return "failed", "error"
    return "ok", ""


def _source_of(tool: str, tin: dict) -> str:
    if tool.startswith("mcp__composio__"):
        slugs = [t.get("tool_slug", "") for t in (tin or {}).get("tools", [])] if isinstance(tin, dict) else []
        return ",".join(sorted(set(slugs))) or tool
    if tool == "Bash":
        cmd = (tin or {}).get("command", "")
        m = re.search(r"scripts/(\w+)\.py", cmd)
        return f"script:{m.group(1)}" if m else "bash"
    return tool


def hook_record(event: dict) -> None:
    path = _ledger_path()
    if not path:
        return
    tool = event.get("tool_name", "")
    tin = event.get("tool_input", {}) or {}
    status, reason = _classify(event.get("tool_response", ""))
    row = {"ts": time.time(), "tool": tool, "source": _source_of(tool, tin), "status": status, "reason": reason}
    if tool.startswith("mcp__composio__") and "MULTI_EXECUTE" in tool:
        tools = tin.get("tools", [])
        resp = event.get("tool_response")
        results = []
        try:
            data = resp if isinstance(resp, dict) else json.loads(resp if isinstance(resp, str) else "{}")
            results = (data.get("data") or {}).get("results", [])
        except Exception:
            pass
        for i, t in enumerate(tools):
            r = results[i] if i < len(results) else {}
            st, why = _classify(r) if r else (status, reason)
            common.append_jsonl(path, {"ts": time.time(), "tool": "composio", "source": t.get("tool_slug", ""),
                                       "status": st, "reason": why, "cost": COMPOSIO_PRICE})
        return
    common.append_jsonl(path, row)


def _composio_calls(path: Path) -> int:
    return sum(1 for r in common.read_jsonl(path) if r.get("tool") == "composio")


def hook_budget(event: dict) -> dict | None:
    path = _ledger_path()
    if not path:
        return None
    k, _ = knobs_mod.load()
    cap = k["budget"]["max_composio_calls"]
    usd_cap = k["budget"]["max_usd_per_run"]
    n = _composio_calls(path)
    asked = len((event.get("tool_input") or {}).get("tools", [])) or 1
    if n + asked > cap or (n + asked) * COMPOSIO_PRICE > usd_cap:
        return {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                "permissionDecisionReason": f"gimme-job budget: {n} Composio calls used, cap {cap} / ${usd_cap}. Stop and report."}}
    return None


def hook_tier(event: dict) -> dict | None:
    tin = event.get("tool_input") or {}
    sub = (tin.get("subagent_type") or "").split(":")[-1]
    if sub not in TIERS:
        return None
    k, _ = knobs_mod.load()
    want = k["models"][TIERS[sub]]
    got = tin.get("model")
    if got and got != want:
        return {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                "permissionDecisionReason": f"tier rule: {sub} runs on {want} (knobs.models.{TIERS[sub]}), not {got}."}}
    return None


def hook_report(event: dict) -> dict | None:
    sub = (event.get("agent_type") or event.get("subagent_type") or "").split(":")[-1]
    if sub not in TIERS or sub == "blind-judge":
        return None
    try:
        d = common.run_dir()
    except SystemExit:
        return None
    reports = d / "reports"
    if not reports.exists() or not any(reports.glob(f"{sub}*")):
        return {"systemMessage": f"gimme-job: {sub} finished without a report file in {reports}. Token rule: full output goes to a file."}
    return None


def summary(run: str | None = None) -> dict:
    path = _ledger_path(run)
    rows = list(common.read_jsonl(path)) if path else []
    by: dict[str, dict] = defaultdict(lambda: {"calls": 0, "ok": 0, "failed": 0, "reasons": defaultdict(int), "cost": 0.0})
    for r in rows:
        key = r.get("source") or r.get("tool", "?")
        b = by[key]
        b["calls"] += 1
        b["ok" if r.get("status") == "ok" else "failed"] += 1
        if r.get("status") != "ok":
            b["reasons"][r.get("reason") or "error"] += 1
        b["cost"] += float(r.get("cost") or 0)
    out = {k: {**v, "reasons": dict(v["reasons"])} for k, v in sorted(by.items())}
    tot = {"calls": sum(v["calls"] for v in out.values()), "ok": sum(v["ok"] for v in out.values()),
           "failed": sum(v["failed"] for v in out.values()), "cost": round(sum(v["cost"] for v in out.values()), 4)}
    return {"by_source": out, "total": tot}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", nargs="?", choices=["summary", "add"])
    for flag in ("--record", "--budget-check", "--tier-check", "--report-check"):
        ap.add_argument(flag, action="store_true")
    ap.add_argument("--run")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--tool")
    ap.add_argument("--status", choices=["ok", "failed", "blocked"])
    ap.add_argument("--reason", default="")
    ap.add_argument("--source", default="")
    ap.add_argument("--cost", type=float, default=0.0)
    a = ap.parse_args(argv)

    if a.record or a.budget_check or a.tier_check or a.report_check:
        try:
            event = json.load(sys.stdin)
        except Exception:
            return 0
        try:
            if a.record:
                hook_record(event)
                return 0
            fn = hook_budget if a.budget_check else hook_tier if a.tier_check else hook_report
            out = fn(event)
            if out:
                print(json.dumps(out))
        except Exception as e:  # a broken hook must never block the session
            print(json.dumps({"systemMessage": f"gimme-job ledger hook error: {e}"}))
        return 0

    if a.cmd == "add":
        path = common.run_dir(a.run, create=True) / "ledger.jsonl"
        common.append_jsonl(path, {"ts": time.time(), "tool": a.tool, "source": a.source or a.tool,
                                   "status": a.status, "reason": a.reason, "cost": a.cost})
        return 0
    s = summary(a.run)
    if a.json:
        print(json.dumps(s, indent=2))
    else:
        for k, v in s["by_source"].items():
            print(f"{k:40} calls={v['calls']:3} ok={v['ok']:3} failed={v['failed']:3} {v['reasons'] or ''}")
        print(f"TOTAL calls={s['total']['calls']} ok={s['total']['ok']} failed={s['total']['failed']} cost=${s['total']['cost']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
