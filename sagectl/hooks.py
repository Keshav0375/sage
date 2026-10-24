"""Hook entry points. settings.json calls `sagectl hook <name>` with the payload on stdin.
Every hook is fail-open on its own bugs (a crashing hook must not brick the session) except the
guard, which is the point."""

from __future__ import annotations

import fnmatch
import json
import re
import subprocess
import sys
import time
from pathlib import Path

from . import gate as gates
from . import guard, paths, trace, ui
from . import project as projects

HANDOFF_HEAD = re.compile(
    r"^\s*(?:```\w*\s*)?(DONE|GAP|HALT|PLANNED|BRIEF|CONTRACT|FINDINGS|CLEAN|VERDICT|REPORT|SCOUT|"
    r"ANSWER|RANKING|SYNTHESIS|CLAIMS|CLUSTERS|PROPOSAL|AGENT|ASK)\b")


def _payload() -> dict:
    try:
        return json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return {}


def _emit(obj: dict) -> None:
    print(json.dumps(obj))


def hook_guard(p: dict) -> int:
    if p.get("tool_name") in ("Skill", "Agent"):
        _safe(trace.from_hook, p)
        return 0
    d = guard.evaluate(p)
    if d.action == "deny":
        _safe(trace.log, "guard_deny", {"tool": p.get("tool_name"), "reason": d.reason[:200]}, p.get("cwd"))
        _emit({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                      "permissionDecisionReason": f"sage guard: {d.reason}"}})
    elif d.action == "rewrite":
        ti = dict(p.get("tool_input") or {})
        ti.update(d.new_input or {})
        _emit({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "allow",
                                      "permissionDecisionReason": f"sage guard: {d.reason}",
                                      "updatedInput": ti}})
    return 0


def hook_session_start(p: dict) -> int:
    name = projects.detect(p.get("cwd"))
    ctx = [ui.card(name)]
    if p.get("source") == "compact":
        snaps = sorted(paths.SNAPSHOTS.glob("*.md")) if paths.SNAPSHOTS.is_dir() else []
        if snaps:
            ctx.append(f"Context was compacted. Last snapshot: {snaps[-1]} — read it before continuing.")
    _emit({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": "\n".join(ctx)}})
    return 0


def hook_post_edit(p: dict) -> int:
    ti = p.get("tool_input") or {}
    f = ti.get("file_path")
    name = projects.detect(p.get("cwd"))
    if not f or not name:
        return 0
    fmt = projects.load(name).format
    for pattern, cmd in fmt.items():
        if any(fnmatch.fnmatch(Path(f).name, g) for g in _expand(pattern)):
            exe = cmd.split()[0]
            if subprocess.run(["which", exe], capture_output=True).returncode == 0:
                subprocess.run(cmd.format(file=f), shell=True, capture_output=True, timeout=60,
                               cwd=str(Path(f).parent))
            break
    return 0


def _expand(pattern: str) -> list[str]:
    m = re.match(r"^(.*)\{(.+)\}(.*)$", pattern)
    return [m.group(1) + x + m.group(3) for x in m.group(2).split(",")] if m else [pattern]


def hook_trace(p: dict) -> int:
    trace.from_hook(p)
    return 0


def hook_subagent_stop(p: dict) -> int:
    """Typed handoffs, enforced: a sage agent's reply must open with its status keyword
    (handoffs/SCHEMA.md). One bounce, then let it through so it can never loop."""
    trace.from_hook(p)
    agent = p.get("agent_type") or ""
    ours = {a.stem for a in (paths.SAGE_HOME / ".claude" / "agents").glob("*.md")}
    if agent not in ours or p.get("stop_hook_active"):
        return 0
    msg = p.get("last_assistant_message") or ""
    if not HANDOFF_HEAD.match(msg):
        _emit({"decision": "block",
               "reason": "sage handoff contract: your final reply must START with your status "
                         "keyword line (e.g. `DONE …`, `FINDINGS …`, `HALT …`) exactly as your "
                         "agent file's Output section shows. Re-send it in that shape."})
    return 0


def hook_stop(p: dict) -> int:
    trace.from_hook(p)
    if p.get("stop_hook_active"):
        return 0
    name = projects.detect(p.get("cwd"))
    if not name:
        return 0
    proj = projects.load(name)
    if not proj.gate.get("stop_gate"):
        return 0
    repo = proj.repo(proj.gate.get("repo"))
    if not repo or not repo.path.is_dir():
        return 0
    dirty = subprocess.run(["git", "status", "--porcelain"], cwd=repo.path, capture_output=True, text=True)
    if not dirty.stdout.strip():
        return 0
    import contextlib
    from io import StringIO
    buf = StringIO()
    with contextlib.redirect_stdout(buf):
        code = gates.run(proj, fast=True, quiet=True)
    if code == 1:
        _emit({"decision": "block",
               "reason": "Fast gate is RED on uncommitted changes — fix before calling it done:\n"
                         + buf.getvalue()[-1500:]})
    return 0


def hook_pre_compact(p: dict) -> int:
    name = projects.detect(p.get("cwd"))
    paths.ensure(paths.SNAPSHOTS)
    lines = [f"# snapshot {time.strftime('%Y-%m-%d %H:%M')} · trigger {p.get('trigger', '?')}", "",
             "```", ui.card(name), "```"]
    if name:
        for r in projects.load(name).repos:
            if r.path.is_dir():
                st = subprocess.run(["git", "status", "-sb"], cwd=r.path, capture_output=True, text=True)
                lines += ["", f"## {r.name} git status", "```", st.stdout.strip()[:2000], "```"]
    f = paths.SNAPSHOTS / f"{time.strftime('%Y%m%d-%H%M%S')}.md"
    f.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 0


def _safe(fn, *a) -> None:
    try:
        fn(*a)
    except Exception:
        pass


HOOKS = {
    "guard": hook_guard,
    "session-start": hook_session_start,
    "post-edit": hook_post_edit,
    "trace": hook_trace,
    "subagent-stop": hook_subagent_stop,
    "stop": hook_stop,
    "pre-compact": hook_pre_compact,
}


def dispatch(name: str) -> int:
    p = _payload()
    fn = HOOKS.get(name)
    if fn is None:
        print(f"unknown hook {name}", file=sys.stderr)
        return 0
    if name == "guard":
        return fn(p)
    try:
        return fn(p)
    except Exception as e:  # fail open, but leave a trace
        _safe(trace.log, "hook_error", {"hook": name, "error": repr(e)[:300]}, p.get("cwd"))
        return 0
