"""PreToolUse guard — the rules a prompt cannot be trusted to keep. Pure functions over the hook
payload, returning a decision; hooks.py turns it into hook JSON.

1. Deletes are moves. A plain `rm` is rewritten to `sagectl trash put`; `rm` inside a compound
   command, `find -delete`, `git clean`, `shred` are denied with the safe alternative.
2. No force. `--force` / `-f` pushes, `reset --hard`, `branch -D` are denied outright.
3. No Claude attribution in commits, PRs or GitHub writes — Keshav is sole author.
4. Held-out evals are sealed: no read, edit or shell access to `evals/**/heldout/**`. The loop
   that improves the harness never sees the test it is graded on.
5. `verified` is the human's word. An agent cannot mark a task verified or sign a phase.
6. Project dead zones (project.toml [guard] dead_zones) are unreadable.
7. Obvious secrets never get written into files.
"""

from __future__ import annotations

import json
import re
import shlex
from dataclasses import dataclass
from pathlib import Path

from . import paths
from . import project as projects

ATTRIBUTION = re.compile(
    r"co-authored-by:\s*claude|generated with \[?claude code|noreply@anthropic\.com", re.I)
FORCE = re.compile(
    r"\bgit\s+push\b[^|;&]*\s(?:--force(?:-with-lease)?|-f)\b|\bgit\s+reset\s+--hard\b"
    r"|\bgit\s+branch\s+-D\b|\bgit\s+checkout\s+--\s|\bgit\s+restore\b(?![^|;&]*--staged)")
DESTRUCTIVE = re.compile(
    r"\bfind\b[^|;&]*\s-delete\b|\bgit\s+clean\b|\bshred\b|\bdiskutil\b[^|;&]*\b(?:erase|delete)"
    r"|\bmkfs\b|\bdd\s+[^|;&]*\bof=|\btruncate\s+-s\s*0\b")
RM = re.compile(r"(?:^|[;&|(]\s*|\bsudo\s+|\bxargs\s+)rm(?:\s|$)")
COMPOUND = re.compile(r"[;&|`$()<>]")
HELDOUT = re.compile(r"(?:^|/)evals/(?:[^/\s]+/)*heldout(?:/|\b)")
VERIFIED = re.compile(r"\bsagectl\b[^|;&]*\b(?:task\b[^|;&]*\bverified\b|phase\s+sign\b)|\bSAGE_HUMAN=")
SECRET = re.compile(
    r"(?:AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{36}|github_pat_[A-Za-z0-9_]{60,}|sk-ant-[A-Za-z0-9-]{20,}"
    r"|sk-[A-Za-z0-9]{32,}|xox[baprs]-[A-Za-z0-9-]{10,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----)")
WRITES_HISTORY = re.compile(
    r"\bgit\s+commit\b|\bgh\s+(?:pr|release|issue)\s+(?:create|edit|comment|merge)\b|\bgh\s+api\b")
FILE_FLAG = re.compile(r"(?:-F|--file|--body-file)[=\s]+(['\"]?)([^\s'\"]+)\1")


@dataclass
class Decision:
    action: str = "allow"            # allow | deny | rewrite
    reason: str = ""
    new_input: dict | None = None


ALLOW = Decision()


def deny(reason: str) -> Decision:
    return Decision("deny", reason)


def _dead_zones(cwd: str) -> list[str]:
    name = projects.detect(cwd)
    if not name:
        return []
    try:
        return projects.load(name).dead_zones
    except SystemExit:
        return []


def _in_zone(path: str, zones: list[str]) -> str | None:
    norm = path.replace("\\", "/")
    for z in zones:
        z = z.rstrip("/")
        if re.search(rf"(?:^|/){re.escape(z)}(?:/|$)", norm):
            return z
    return None


def check_bash(cmd: str, cwd: str) -> Decision:
    if WRITES_HISTORY.search(cmd):
        text = cmd
        for _, f in FILE_FLAG.findall(cmd):
            fp = Path(f) if Path(f).is_absolute() else Path(cwd) / f
            if fp.is_file():
                text += "\n" + fp.read_text(encoding="utf-8", errors="replace")
        if ATTRIBUTION.search(text):
            return deny("Claude attribution in a commit/PR. Keshav is sole author — drop the "
                        "Co-Authored-By / 'Generated with Claude Code' line.")
    if VERIFIED.search(cmd):
        return deny("`verified` and phase sign-off are Keshav's call, not an agent's. Set the task "
                    "to `review` and tell him what to check.")
    if FORCE.search(cmd):
        return deny("Force/destructive git op blocked (push --force, reset --hard, branch -D, "
                    "checkout --, restore). Make a new commit or ask Keshav to run it himself.")
    if DESTRUCTIVE.search(cmd):
        return deny("Destructive command blocked (find -delete, git clean, shred, disk erase, dd, "
                    "truncate). Move files with `sagectl trash put <paths>` instead.")
    if HELDOUT.search(cmd):
        return deny("evals/**/heldout is sealed. Run it only through `sagectl eval run --split heldout`.")
    zones = _dead_zones(cwd)
    for tok in _tokens(cmd):
        if z := _in_zone(tok, zones):
            return deny(f"`{z}` is a dead zone for this project (project.toml [guard]).")
    if RM.search(cmd):
        return _rewrite_rm(cmd, cwd)
    return ALLOW


def _tokens(cmd: str) -> list[str]:
    try:
        return shlex.split(cmd)
    except ValueError:
        return cmd.split()


def _rewrite_rm(cmd: str, cwd: str) -> Decision:
    stripped = cmd.strip()
    if COMPOUND.search(stripped) or not stripped.startswith("rm "):
        return deny("`rm` inside a compound command is blocked. Run the delete on its own line — "
                    "it becomes a reversible `sagectl trash put`.")
    args = _tokens(stripped)[1:]
    targets = [a for a in args if not a.startswith("-")]
    if not targets:
        return deny("rm with no targets.")
    sagectl = paths.SAGE_HOME / "bin" / "sagectl"
    new = "python3 " + shlex.quote(str(sagectl)) + " trash put --cwd " + shlex.quote(cwd) + " -- " + \
        " ".join(shlex.quote(t) for t in targets)
    return Decision("rewrite", "rm rewritten to a reversible trash move (.sage/trash)", {"command": new})


def check_path(tool: str, path: str | None, cwd: str, content: str = "") -> Decision:
    if not path:
        return ALLOW
    if HELDOUT.search(path.replace("\\", "/")):
        return deny("evals/**/heldout is sealed — the improver never sees its own test set.")
    if z := _in_zone(path, _dead_zones(cwd)):
        return deny(f"`{z}` is a dead zone for this project (project.toml [guard]).")
    if tool in ("Write", "Edit") and content and SECRET.search(content):
        return deny("That content contains what looks like a live secret. Use an env var / secret "
                    "store reference instead.")
    return ALLOW


def evaluate(payload: dict) -> Decision:
    tool = payload.get("tool_name", "")
    ti = payload.get("tool_input") or {}
    cwd = payload.get("cwd") or str(paths.SAGE_HOME)
    if tool == "Bash":
        return check_bash(ti.get("command", ""), cwd)
    if tool in ("Read", "Edit", "Write", "NotebookEdit"):
        content = ti.get("content") or ti.get("new_string") or ""
        return check_path(tool, ti.get("file_path") or ti.get("notebook_path"), cwd, content)
    if tool in ("Grep", "Glob"):
        target = " ".join(str(ti.get(k) or "") for k in ("path", "glob", "pattern"))
        if HELDOUT.search(target):
            return deny("evals/**/heldout is sealed.")
        return check_path(tool, ti.get("path"), cwd)
    if tool.startswith("mcp__github__"):
        if ATTRIBUTION.search(json.dumps(ti)):
            return deny("Claude attribution in a GitHub write. Keshav is sole author.")
    return ALLOW
