"""Traces and lessons — the raw material of weakness mining.

traces: .sage/traces/<day>.jsonl, written by hooks. Local-only, gitignored. Captures tool
failures, user corrections, subagent results, skill/agent usage, gate verdicts.

lessons: projects/<p>/lessons.jsonl, committed. One structured entry per mistake — what
happened, root cause, the rule that prevents a repeat. Repeats graduate into rules/hooks via
/retro; clusters of them feed /evolve.
"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path

from . import paths
from . import project as projects

CORRECTION = re.compile(
    r"^\s*(?:no\b|nope|wrong|that'?s not|not what i|you (?:broke|missed|forgot|ignored)|why did you"
    r"|revert|undo|stop\b|don'?t\b|again\?|bro,? (?:no|what)|wtf)", re.I)


def log(event: str, data: dict, cwd: str | None = None) -> None:
    paths.ensure(paths.TRACES)
    rec = {"ts": int(time.time()), "event": event, "project": projects.detect(cwd) if cwd else None, **data}
    day = time.strftime("%Y-%m-%d")
    with (paths.TRACES / f"{day}.jsonl").open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")


def read(days: int = 30, project: str | None = None, event: str | None = None) -> list[dict]:
    if not paths.TRACES.is_dir():
        return []
    cutoff = time.time() - days * 86400
    out = []
    for f in sorted(paths.TRACES.glob("*.jsonl")):
        for line in f.read_text(encoding="utf-8").splitlines():
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            if r.get("ts", 0) < cutoff:
                continue
            if project and r.get("project") != project:
                continue
            if event and r.get("event") != event:
                continue
            out.append(r)
    return out


def from_hook(payload: dict) -> None:
    """Map a hook payload to a compact trace record. Never raises."""
    ev = payload.get("hook_event_name", "")
    cwd = payload.get("cwd")
    if ev == "PostToolUseFailure":
        err = payload.get("error") or payload.get("tool_response") or ""
        log("tool_failure", {"tool": payload.get("tool_name"),
                             "input": _short(payload.get("tool_input")),
                             "error": _short(err, 600)}, cwd)
    elif ev == "UserPromptSubmit":
        prompt = payload.get("prompt", "")
        if CORRECTION.search(prompt):
            log("correction", {"prompt": prompt[:400]}, cwd)
    elif ev == "SubagentStop":
        log("subagent", {"agent": payload.get("agent_type"),
                         "head": (payload.get("last_assistant_message") or "")[:300]}, cwd)
    elif ev == "PreToolUse" and payload.get("tool_name") in ("Skill", "Agent"):
        ti = payload.get("tool_input") or {}
        log("use", {"tool": payload.get("tool_name"),
                    "name": ti.get("skill") or ti.get("subagent_type") or "general-purpose"}, cwd)
    elif ev in ("Stop", "SessionEnd"):
        log(ev.lower(), {"reason": payload.get("reason")}, cwd)


def _short(v, n: int = 300) -> str:
    s = v if isinstance(v, str) else json.dumps(v, ensure_ascii=False)
    return s[:n]


# --- lessons --------------------------------------------------------------------------------

def lessons_file(project: str) -> Path:
    return paths.PROJECTS / project / "lessons.jsonl"


def add_lesson(project: str, what: str, root_cause: str, rule: str, tags: list[str],
               severity: str = "minor", source: str = "manual") -> dict:
    projects.load(project)
    f = lessons_file(project)
    existing = load_lessons(project)
    rec = {"id": f"L{len(existing) + 1:03d}", "ts": int(time.time()), "date": time.strftime("%Y-%m-%d"),
           "what": what, "root_cause": root_cause, "rule": rule, "tags": tags,
           "severity": severity, "source": source, "status": "open"}
    with f.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return rec


def load_lessons(project: str) -> list[dict]:
    f = lessons_file(project)
    if not f.is_file():
        return []
    return [json.loads(x) for x in f.read_text(encoding="utf-8").splitlines() if x.strip()]


def set_lesson_status(project: str, lesson_id: str, status: str) -> None:
    rows = load_lessons(project)
    for r in rows:
        if r["id"] == lesson_id:
            r["status"] = status
            break
    else:
        raise SystemExit(f"no lesson {lesson_id}")
    lessons_file(project).write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))
