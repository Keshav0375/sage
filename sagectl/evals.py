"""Held-in / held-out evals: the referee for every harness change.

An eval task is a folder with task.toml:

    id = "py-001"
    prompt = "Add a /health endpoint that returns {'ok': true} and a test for it."
    workdir = "fixture"            # copied fresh into a temp dir per run (relative to task dir)
    verify = "pytest -q"           # exit 0 == pass; runs in the temp dir after the agent
    cluster = "C3"                 # the failure mechanism it came from (optional)
    timeout = 900

Tasks live in evals/harness/{heldin,heldout}/ (harness-wide) or projects/<p>/evals/{heldin,heldout}/.
`heldin` is what the harness-smith may look at while proposing. `heldout` is sealed by the guard
and only ever executed here.

A run executes `claude -p` headless against each task with the harness under test (a git ref of
sage checked out as a worktree), then the verifier. Results land in .sage/evals/<label>/.
`compare` applies the promotion rule: an edit is promoted only if held-in improves and NO
held-out task that passed before fails now (Self-Harness: no measurable regression).
"""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import time
import tomllib
from pathlib import Path

from . import paths

SPLITS = ("heldin", "heldout")


def roots(project: str | None) -> list[Path]:
    return [paths.PROJECTS / project / "evals"] if project else [paths.HARNESS_EVALS]


def tasks(project: str | None, split: str) -> list[tuple[Path, dict]]:
    out = []
    for root in roots(project):
        d = root / split
        for t in sorted(d.glob("*/task.toml")) if d.is_dir() else []:
            out.append((t.parent, tomllib.loads(t.read_text(encoding="utf-8"))))
    return out


def run(project: str | None, split: str, label: str, harness: Path | None = None,
        trials: int = 1, model: str | None = None) -> int:
    if split not in SPLITS:
        raise SystemExit(f"split must be one of {SPLITS}")
    ts = tasks(project, split)
    if not ts:
        print(f"no {split} tasks for {project or 'harness'}")
        return 3
    if shutil.which("claude") is None:
        print("`claude` CLI not found — evals need headless Claude Code (`claude -p`).")
        return 3
    out_dir = paths.ensure(paths.EVAL_RESULTS / label / split)
    harness = harness or paths.SAGE_HOME
    passed = 0
    for tdir, spec in ts:
        wins = 0
        for n in range(trials):
            ok, secs = _one(tdir, spec, harness, model)
            wins += ok
            print(f"  {'PASS' if ok else 'FAIL'} {spec['id']} (trial {n + 1}, {secs:.0f}s)")
        rate = wins / trials
        passed += rate >= 0.5
        (out_dir / f"{spec['id']}.json").write_text(json.dumps(
            {"id": spec["id"], "pass_rate": rate, "trials": trials, "cluster": spec.get("cluster"),
             "at": int(time.time())}))
    print(f"EVAL {label} · {split} · {passed}/{len(ts)} passed")
    return 0


def _one(tdir: Path, spec: dict, harness: Path, model: str | None) -> tuple[bool, float]:
    t0 = time.time()
    with tempfile.TemporaryDirectory(prefix="sage-eval-") as tmp:
        work = Path(tmp) / "work"
        src = tdir / spec.get("workdir", "fixture")
        if src.is_dir():
            shutil.copytree(src, work)
        else:
            work.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=work)
        cmd = ["claude", "-p", spec["prompt"], "--output-format", "json",
               "--add-dir", str(harness), "--permission-mode", "acceptEdits"]
        if model:
            cmd += ["--model", model]
        env = {"SAGE_HOME": str(harness), "SAGE_EVAL": "1"}
        try:
            subprocess.run(cmd, cwd=work, capture_output=True, text=True,
                           timeout=spec.get("timeout", 900), env={**_env(), **env})
        except subprocess.TimeoutExpired:
            return False, time.time() - t0
        v = subprocess.run(spec["verify"], shell=True, cwd=work, capture_output=True, text=True,
                           timeout=600)
        return v.returncode == 0, time.time() - t0


def _env() -> dict:
    import os
    return dict(os.environ)


def load_results(label: str, split: str) -> dict[str, float]:
    d = paths.EVAL_RESULTS / label / split
    if not d.is_dir():
        return {}
    return {json.loads(f.read_text())["id"]: json.loads(f.read_text())["pass_rate"] for f in d.glob("*.json")}


def compare(base: dict[str, dict[str, float]], cand: dict[str, dict[str, float]]) -> tuple[str, list[str]]:
    """Promotion rule. base/cand: {"heldin": {id: rate}, "heldout": {id: rate}}."""
    notes = []
    bi, ci = base.get("heldin", {}), cand.get("heldin", {})
    bo, co = base.get("heldout", {}), cand.get("heldout", {})
    gain = sum(ci.get(k, 0) for k in bi) - sum(bi.values())
    regress = [k for k, v in bo.items() if v >= 0.5 and co.get(k, 0) < 0.5]
    out_delta = sum(co.get(k, 0) for k in bo) - sum(bo.values())
    notes.append(f"held-in Δ {gain:+.2f} over {len(bi)} task(s)")
    notes.append(f"held-out Δ {out_delta:+.2f} over {len(bo)} task(s)")
    if not bo:
        return "REJECT", notes + ["no held-out results — an edit is never promoted blind"]
    if regress:
        return "REJECT", notes + [f"held-out regressions: {', '.join(sorted(regress))}"]
    if gain <= 0 and out_delta <= 0:
        return "REJECT", notes + ["no improvement on either split"]
    return "PROMOTE", notes


def compare_labels(base: str, cand: str) -> int:
    b = {s: load_results(base, s) for s in SPLITS}
    c = {s: load_results(cand, s) for s in SPLITS}
    verdict, notes = compare(b, c)
    for n in notes:
        print("  " + n)
    print(f"VERDICT {verdict} · {cand} vs {base}")
    return 0 if verdict == "PROMOTE" else 1


def assign_split(task_id: str) -> str:
    """Deterministic, not chosen: roughly one task in three is sealed into heldout. No agent
    gets to decide which of its own tasks it will be graded on."""
    import hashlib
    return "heldout" if int(hashlib.sha256(task_id.encode()).hexdigest(), 16) % 3 == 0 else "heldin"


def new(project: str | None, task_id: str, prompt: str, verify: str, cluster: str = "") -> Path:
    split = assign_split(task_id)
    root = roots(project)[0] / split / task_id
    if root.exists():
        raise SystemExit(f"{root} exists")
    (root / "fixture").mkdir(parents=True)
    body = (f'id = "{task_id}"\nprompt = """{prompt}"""\nworkdir = "fixture"\n'
            f'verify = "{verify}"\ncluster = "{cluster}"\ntimeout = 900\n')
    (root / "task.toml").write_text(body)
    (root / "fixture" / ".keep").write_text("")
    return root
