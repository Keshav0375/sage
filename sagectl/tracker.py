"""Phase tracker: projects/<p>/phases/TODO.md is the single source of truth.

    ## Phase 1 — Bootstrap
    branch: dev/phase-1-bootstrap · repo: backend · target: 2026-11-01
    signed: 2026-11-02                       (only once the human signs the phase off)
    - [verified] 1.1 Scaffold the app
    - [wip] 1.2 Auth middleware · deps 1.1
    - [todo] 1.3 Public API · deps 1.1, 1.2

Statuses: todo · wip · blocked · review · verified. `verified` is the human's to set.
The active phase is the first one without a `signed:` line. WAVES layers its unbuilt tasks by
their `deps`, so every task in a wave depends only on earlier waves — a wave is built in parallel.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

STATUSES = ("todo", "wip", "blocked", "review", "verified")
UNBUILT = ("todo", "wip", "blocked")

PHASE = re.compile(r"^##\s+Phase\s+(\d+)\s*[—–-]\s*(.+?)\s*$")
TASK = re.compile(r"^-\s+\[(\w+)\]\s+(\d+\.\d+)\s+(.+?)(?:\s+·\s+deps\s+(.+))?\s*$")
META = re.compile(r"(\w+):\s*([^·]+?)\s*(?:·|$)")


@dataclass
class Task:
    id: str
    title: str
    status: str
    deps: list[str] = field(default_factory=list)
    line: int = 0


@dataclass
class Phase:
    num: int
    title: str
    meta: dict = field(default_factory=dict)
    tasks: list[Task] = field(default_factory=list)

    @property
    def signed(self) -> bool:
        return "signed" in self.meta

    @property
    def branch(self) -> str:
        return self.meta.get("branch", f"dev/phase-{self.num}")


def parse(todo: Path) -> list[Phase]:
    phases: list[Phase] = []
    if not todo.is_file():
        return phases
    for i, line in enumerate(todo.read_text(encoding="utf-8").splitlines(), 1):
        if m := PHASE.match(line):
            phases.append(Phase(int(m.group(1)), m.group(2)))
        elif phases and (m := TASK.match(line)):
            deps = [d.strip() for d in (m.group(4) or "").split(",") if d.strip()]
            phases[-1].tasks.append(Task(m.group(2), m.group(3), m.group(1).lower(), deps, i))
        elif phases and not phases[-1].tasks and ":" in line and not line.startswith("#"):
            phases[-1].meta.update({k: v.strip() for k, v in META.findall(line)})
    return phases


def active(phases: list[Phase]) -> Phase | None:
    return next((p for p in phases if not p.signed), None)


def waves(phase: Phase) -> tuple[list[list[str]], list[str]]:
    """Layer the phase's unbuilt tasks by same-phase deps. Returns (waves, cycle).
    Deps on tasks outside the phase, or already built, are satisfied. A cycle is never guessed
    through: its tasks are returned separately, to run one at a time in id order."""
    ids = {t.id for t in phase.tasks}
    pending = {t.id: {d for d in t.deps if d in ids} for t in phase.tasks if t.status in UNBUILT}
    built = {t.id for t in phase.tasks if t.status not in UNBUILT}
    layers: list[list[str]] = []
    while pending:
        ready = sorted((t for t, d in pending.items() if d <= built), key=_key)
        if not ready:
            return layers, sorted(pending, key=_key)
        layers.append(ready)
        built.update(ready)
        for t in ready:
            del pending[t]
    return layers, []


def _key(tid: str) -> tuple[int, ...]:
    return tuple(int(x) for x in tid.split("."))


def set_status(todo: Path, task_id: str, status: str) -> str:
    if status not in STATUSES:
        raise SystemExit(f"status must be one of {', '.join(STATUSES)}")
    lines = todo.read_text(encoding="utf-8").splitlines(keepends=True)
    for i, line in enumerate(lines):
        m = TASK.match(line.rstrip("\n"))
        if m and m.group(2) == task_id:
            old = m.group(1)
            lines[i] = line.replace(f"[{old}]", f"[{status}]", 1)
            todo.write_text("".join(lines), encoding="utf-8")
            return old
    raise SystemExit(f"task {task_id} not found in {todo}")
