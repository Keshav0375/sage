"""Where things live. SAGE_HOME is the brain repo root; `.sage/` is local, gitignored runtime state."""

from __future__ import annotations

import os
from pathlib import Path

SAGE_HOME = Path(os.environ.get("SAGE_HOME") or Path(__file__).resolve().parent.parent)
PROJECTS = SAGE_HOME / "projects"
LIBRARY = SAGE_HOME / "library"
TEMPLATES = SAGE_HOME / "_templates"
HARNESS_EVALS = SAGE_HOME / "evals" / "harness"
RUNTIME = SAGE_HOME / ".sage"
TRACES = RUNTIME / "traces"
TRASH = RUNTIME / "trash"
CACHE = RUNTIME / "cache"
SNAPSHOTS = RUNTIME / "handoffs"
EVAL_RESULTS = RUNTIME / "evals"


def ensure(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path
