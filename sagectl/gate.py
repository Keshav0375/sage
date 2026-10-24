"""The quality gate, done right: the project's own commands from project.toml, run in the right
repo, ending in ONE verdict line. Green means green — a step whose tool is missing is SKIP and
makes the verdict PARTIAL, never GREEN."""

from __future__ import annotations

import json
import shlex
import shutil
import subprocess
import time
from pathlib import Path

from . import paths
from .project import Project

TAIL = 25  # lines of failing output to show


def run(proj: Project, fast: bool = False, path: str | None = None, quiet: bool = False) -> int:
    gate = proj.gate
    steps = gate.get("fast" if fast else "full") or gate.get("full") or []
    if not steps:
        print(f"VERDICT INCONCLUSIVE · project '{proj.name}' has no [gate] commands in project.toml")
        return 3
    repo = proj.repo(gate.get("repo"))
    cwd = Path(path) if path else (repo.path if repo else proj.root)
    if not cwd.is_dir():
        print(f"VERDICT INCONCLUSIVE · gate dir missing: {cwd}")
        return 3

    results = []
    for cmd in steps:
        exe = shlex.split(cmd)[0]
        if shutil.which(exe) is None and not (cwd / exe).exists():
            results.append(("SKIP", cmd, f"`{exe}` not installed"))
            continue
        t0 = time.time()
        p = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
        dt = time.time() - t0
        if p.returncode == 0:
            results.append(("OK", cmd, f"{dt:.1f}s"))
        else:
            out = (p.stdout + p.stderr).strip().splitlines()[-TAIL:]
            results.append(("FAIL", cmd, "\n      ".join(out)))

    for status, cmd, info in results:
        if not quiet or status != "OK":
            print(f"  {status:<4} {cmd}  {info if status != 'OK' else '· ' + info}")

    fails = [r for r in results if r[0] == "FAIL"]
    skips = [r for r in results if r[0] == "SKIP"]
    if fails:
        verdict, code = "RED", 1
    elif skips:
        verdict, code = "PARTIAL", 2
    else:
        verdict, code = "GREEN", 0
    mode = "fast" if fast else "full"
    summary = f"{len(results) - len(fails) - len(skips)}/{len(results)} ok"
    if skips:
        summary += " · skipped: " + ", ".join(s[1] for s in skips)
    print(f"VERDICT {verdict} · {proj.name} · {mode} · {summary}")

    paths.ensure(paths.CACHE)
    (paths.CACHE / f"gate-{proj.name}.json").write_text(json.dumps(
        {"verdict": verdict, "mode": mode, "at": int(time.time())}))
    return code
