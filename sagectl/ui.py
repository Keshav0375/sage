"""Terminal surfaces: the statusline (rendered every few hundred ms, so it never shells out to
git — it reads .git/HEAD and cached state only) and the session card (SessionStart + /start)."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

from . import paths, trace, tracker
from . import project as projects

C = {"dim": "\033[2m", "b": "\033[1m", "g": "\033[32m", "y": "\033[33m", "r": "\033[31m",
     "c": "\033[36m", "m": "\033[35m", "x": "\033[0m"}
if os.environ.get("NO_COLOR"):
    C = {k: "" for k in C}


def _branch(start: Path) -> str | None:
    for d in [start, *start.parents]:
        head = d / ".git"
        if head.is_file():  # worktree: "gitdir: <path>"
            gd = Path(head.read_text().split(":", 1)[1].strip())
            head = gd
        if (head / "HEAD").is_file():
            ref = (head / "HEAD").read_text().strip()
            return ref.rsplit("/", 1)[-1] if ref.startswith("ref:") else ref[:7]
    return None


def _gate(name: str) -> str:
    f = paths.CACHE / f"gate-{name}.json"
    if not f.is_file():
        return f"{C['dim']}gate –{C['x']}"
    g = json.loads(f.read_text())
    col = {"GREEN": "g", "RED": "r"}.get(g["verdict"], "y")
    sym = {"GREEN": "✓", "RED": "✗"}.get(g["verdict"], "~")
    age = int((time.time() - g["at"]) / 60)
    return f"{C[col]}gate {sym}{C['x']}{C['dim']}{age}m{C['x']}"


def _pct(v, warn=60, hot=85) -> str:
    if v is None:
        return "–"
    v = float(v)
    col = "r" if v >= hot else "y" if v >= warn else "g"
    return f"{C[col]}{v:.0f}%{C['x']}"


def statusline(payload: dict) -> str:
    ws = payload.get("workspace") or {}
    cwd = Path(ws.get("current_dir") or payload.get("cwd") or os.getcwd())
    name = projects.detect(cwd)
    parts = [f"{C['m']}{C['b']}sage{C['x']}"]
    if name:
        seg = f"{C['c']}{name}{C['x']}"
        try:
            ph = tracker.active(tracker.parse(paths.PROJECTS / name / "phases" / "TODO.md"))
            if ph:
                cur = next((t for t in ph.tasks if t.status in ("wip", "review", "blocked")), None)
                seg += f" P{ph.num}" + (f" {cur.id} {cur.status}" if cur else "")
        except Exception:
            pass
        parts.append(seg)
        parts.append(_gate(name))
    if br := _branch(cwd):
        parts.append(f"⎇ {br}")
    if agent := (payload.get("agent") or {}).get("name"):
        parts.append(f"{C['y']}↳ {agent}{C['x']}")
    cw = payload.get("context_window") or {}
    parts.append(f"ctx {_pct(cw.get('used_percentage'))}")
    rl = (payload.get("rate_limits") or {}).get("five_hour") or {}
    if rl:
        parts.append(f"5h {_pct(rl.get('used_percentage'), 50, 80)}")
    cost = (payload.get("cost") or {}).get("total_cost_usd")
    if cost is not None:
        parts.append(f"{C['dim']}${cost:.2f}{C['x']}")
    return " · ".join(parts)


def card(name: str | None) -> str:
    w = 64
    top = "╭─ sage " + "─" * (w - 9) + "╮"
    rows: list[str] = []
    if not name:
        rows += ["no active project — you're in the brain root.",
                 f"projects: {', '.join(projects.names()) or 'none yet'}",
                 "`/new-project <name>` or `sagectl use <name>`"]
    else:
        proj = projects.load(name)
        rows.append(f"project  {name} · {proj.kind}" + (f" · {proj.description[:40]}" if proj.description else ""))
        for r in proj.repos:
            rows.append(f"repo     {r.name} → {r.path}" + ("" if r.path.is_dir() else "  (missing!)"))
        phases = tracker.parse(proj.root / "phases" / "TODO.md")
        ph = tracker.active(phases)
        if ph:
            done = sum(t.status == "verified" for t in ph.tasks)
            rows.append(f"phase    {ph.num} — {ph.title} · {done}/{len(ph.tasks)} verified")
            rows.append(f"branch   {ph.branch}")
            lw, cyc = tracker.waves(ph)
            if lw:
                rows.append("waves    " + " | ".join(f"{i + 1}: {' '.join(x)}" for i, x in enumerate(lw)))
            if cyc:
                rows.append(f"CYCLE    {' '.join(cyc)} — fix deps")
            for t in ph.tasks:
                if t.status in ("wip", "review", "blocked"):
                    rows.append(f"  {t.status:<8} {t.id} {t.title[:44]}")
        else:
            rows.append("phase    none open — `/plan` the next one")
        open_l = [l for l in trace.load_lessons(name) if l.get("status") == "open"]
        rows.append(f"lessons  {len(open_l)} open" + (f" · latest: {open_l[-1]['rule'][:36]}" if open_l else ""))
        g = paths.CACHE / f"gate-{name}.json"
        if g.is_file():
            gd = json.loads(g.read_text())
            rows.append(f"gate     {gd['verdict']} ({gd['mode']}) {int((time.time() - gd['at']) / 3600)}h ago")
    trash_n = len(list(paths.TRASH.iterdir())) if paths.TRASH.is_dir() else 0
    if trash_n:
        rows.append(f"trash    {trash_n} bucket(s) · `sagectl trash list`")
    body = [f"│ {r[:w - 4]:<{w - 4}} │" for r in rows]
    return "\n".join([top, *body, "╰" + "─" * (w - 2) + "╯"])


# --- projects board: every project on one card -----------------------------------------------

def _ago(ts: float | None) -> str:
    if not ts:
        return "never"
    s = int(time.time() - ts)
    for unit, n in (("d", 86400), ("h", 3600), ("m", 60)):
        if s >= n:
            return f"{s // n}{unit}"
    return "now"


def _bar(done: int, total: int, width: int = 12) -> str:
    fill = round(width * done / total) if total else 0
    return "█" * fill + "░" * (width - fill)


def summary(name: str) -> dict:
    """Everything the board shows about one project, as data (also `sagectl projects --json`)."""
    proj = projects.load(name)
    phases = tracker.parse(proj.root / "phases" / "TODO.md")
    ph = tracker.active(phases)
    lessons = trace.load_lessons(name)
    gate_f = paths.CACHE / f"gate-{name}.json"
    gate = json.loads(gate_f.read_text()) if gate_f.is_file() else None
    files = [proj.root / f for f in ("phases/TODO.md", "STATE.md", "lessons.jsonl", "project.toml")]
    touched = max((f.stat().st_mtime for f in files if f.is_file()), default=None)
    out = {
        "name": name, "kind": proj.kind, "description": proj.description,
        "repos": [{"name": r.name, "path": str(r.path), "ok": r.path.is_dir()} for r in proj.repos],
        "phases_total": len(phases), "phases_signed": sum(p.signed for p in phases),
        "phase": None, "open_lessons": sum(lsn.get("status") == "open" for lsn in lessons),
        "gate": gate, "touched": touched,
    }
    if ph:
        lw, cyc = tracker.waves(ph)
        out["phase"] = {
            "num": ph.num, "title": ph.title, "branch": ph.branch,
            "verified": sum(t.status == "verified" for t in ph.tasks), "tasks": len(ph.tasks),
            "now": [{"id": t.id, "status": t.status, "title": t.title}
                    for t in ph.tasks if t.status in ("wip", "review", "blocked")],
            "next_wave": lw[0] if lw else [], "cycle": cyc,
        }
    return out


def board(active: str | None = None) -> str:
    names = projects.names()
    w = 72
    title = f"─ sage · {len(names)} project{'s' if len(names) != 1 else ''} "
    top = "╭" + title + "─" * (w - 2 - len(title)) + "╮"
    if not names:
        rows = ["no projects yet — `/new-project <name>` to start one"]
        return "\n".join([top, *[f"│ {r:<{w - 4}} │" for r in rows], "╰" + "─" * (w - 2) + "╯"])

    sums = [summary(n) for n in names]
    # active first, then most recently touched
    sums.sort(key=lambda s: (s["name"] != active, -(s["touched"] or 0)))
    rows: list[str] = []
    for i, s in enumerate(sums):
        if i:
            rows.append("─" * (w - 4))
        mark = "▸" if s["name"] == active else " "
        desc = f"  {s['description']}" if s["description"] else ""
        rows.append(f"{mark} {s['name']:<16} {s['kind']:<8}{desc}")
        ph = s["phase"]
        if ph:
            of = f"{ph['num']}/{s['phases_total']}"
            rows.append(f"  phase  {of} — {ph['title'][:22]:<22} {_bar(ph['verified'], ph['tasks'])} "
                        f"{ph['verified']}/{ph['tasks']}")
            now = " · ".join(f"{t['id']} {t['status']} {t['title'][:18]}" for t in ph["now"][:2])
            nxt = f"next wave {' '.join(ph['next_wave'])}" if ph["next_wave"] else ""
            if ph["cycle"]:
                nxt = f"CYCLE {' '.join(ph['cycle'])}"
            if now or nxt:
                rows.append("  now    " + " · ".join(x for x in (now, nxt) if x))
        elif s["phases_total"]:
            rows.append(f"  phase  all {s['phases_total']} signed ✓ — `/plan` the next one")
        else:
            rows.append("  phase  none yet — `/spec` then `/plan`")
        g = s["gate"]
        gate = f"gate {'✓' if g['verdict'] == 'GREEN' else '✗' if g['verdict'] == 'RED' else '~'} " \
               f"{g['verdict']} {_ago(g['at'])}" if g else "gate –"
        bad = [r["name"] for r in s["repos"] if not r["ok"]]
        repos = "no repos"
        if s["repos"]:
            repos = f"repos {len(s['repos'])}" + (f" (missing: {', '.join(bad)})" if bad else " ok")
        rows.append(f"  {gate} · lessons {s['open_lessons']} open · {repos} · touched {_ago(s['touched'])}")

    verified = sum(s["phase"]["verified"] for s in sums if s["phase"])
    tasks = sum(s["phase"]["tasks"] for s in sums if s["phase"])
    lessons = sum(s["open_lessons"] for s in sums)
    red = sum(1 for s in sums if s["gate"] and s["gate"]["verdict"] == "RED")
    foot = (f" {verified}/{tasks} active tasks verified · {lessons} lesson{'s' if lessons != 1 else ''} open · "
            f"{red} RED gate{'s' if red != 1 else ''} ")
    bottom = "╰" + "─" * (w - 3 - len(foot)) + foot + "─╯"
    body = [f"│ {r[:w - 4]:<{w - 4}} │" for r in rows]
    return "\n".join([top, *body, bottom])
