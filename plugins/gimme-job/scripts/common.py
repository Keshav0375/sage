"""Shared helpers: paths, run folders, JSONL I/O."""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Iterable, Iterator

PLUGIN = Path(__file__).resolve().parent.parent
if str(PLUGIN) not in sys.path:
    sys.path.insert(0, str(PLUGIN))

from scripts import knobs as knobs_mod  # noqa: E402


def repo_root() -> Path:
    return knobs_mod.repo_root()


def data_root(k: dict | None = None) -> Path:
    env = os.environ.get("GIMME_JOB_DATA")
    if env:
        return Path(env)
    rel = (k or {}).get("resume", {}).get("data_root", "memory/resume")
    return repo_root() / rel


def runs_dir(k: dict | None = None) -> Path:
    return data_root(k) / "runs"


def current_run_file(k: dict | None = None) -> Path:
    return runs_dir(k) / "CURRENT"


def new_run(k: dict | None = None) -> Path:
    base = time.strftime("%Y%m%d-%H%M%S")
    rid, n = base, 1
    while (runs_dir(k) / rid).exists():
        n += 1
        rid = f"{base}-{n}"
    d = runs_dir(k) / rid
    d.mkdir(parents=True)
    current_run_file(k).write_text(rid)
    return d


def run_dir(run_id: str | None = None, k: dict | None = None, create: bool = False) -> Path:
    if not run_id:
        f = current_run_file(k)
        if not f.exists():
            if create:
                return new_run(k)
            raise SystemExit("no current run; start one with scan.py or pass --run")
        run_id = f.read_text().strip()
    d = runs_dir(k) / run_id
    if create:
        d.mkdir(parents=True, exist_ok=True)
    return d


def read_jsonl(path: Path) -> Iterator[dict]:
    if not path.exists():
        return
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    yield json.loads(line)
                except json.JSONDecodeError:
                    continue


def write_jsonl(path: Path, rows: Iterable[dict]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
            n += 1
    return n


def append_jsonl(path: Path, row: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def read_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
