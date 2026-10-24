"""sagectl — one CLI for the deterministic half of sage. Agents call it through Bash; skills
document it; hooks run it. (CLI + skill beats an MCP server on tokens when a shell exists —
an MCP wrapper over these same functions can come later, if a no-shell client needs it.)"""

from __future__ import annotations

import argparse
import json
import sys

from . import __version__, paths


def _project(args) -> str:
    from . import project as projects
    name = getattr(args, "project", None) or projects.detect()
    if not name:
        raise SystemExit("no project — pass -p <name>, cd into it, or `sagectl use <name>`")
    return name


def cmd_where(a) -> int:
    from . import project as projects
    from . import tracker, ui
    if a.all:
        for n in projects.names():
            for ph in tracker.parse(paths.PROJECTS / n / "phases" / "TODO.md"):
                done = sum(t.status == "verified" for t in ph.tasks)
                state = "signed" if ph.signed else "open"
                print(f"{n:<16} P{ph.num:<3} {state:<7} {done}/{len(ph.tasks)}  {ph.title}")
        return 0
    name = _project(a)
    phases = tracker.parse(paths.PROJECTS / name / "phases" / "TODO.md")
    ph = next((p for p in phases if p.num == a.phase), None) if a.phase else tracker.active(phases)
    if a.json:
        if not ph:
            print("{}")
            return 1
        lw, cyc = tracker.waves(ph)
        print(json.dumps({"project": name, "phase": ph.num, "title": ph.title, "meta": ph.meta,
                          "tasks": [t.__dict__ for t in ph.tasks], "waves": lw, "cycle": cyc}))
        return 0
    print(ui.card(name))
    if not ph:
        return 1
    prev = [p for p in phases if p.num < ph.num and not p.signed]
    if prev:
        print(f"HALT  phase {prev[0].num} is not signed off — sign it before entering {ph.num}")
        return 1
    return 0


def cmd_task(a) -> int:
    from . import tracker
    name = _project(a)
    old = tracker.set_status(paths.PROJECTS / name / "phases" / "TODO.md", a.id, a.status)
    print(f"{name} {a.id}: {old} → {a.status}")
    return 0


def cmd_phase(a) -> int:
    import re
    import time

    from . import tracker
    name = _project(a)
    todo = paths.PROJECTS / name / "phases" / "TODO.md"
    phases = tracker.parse(todo)
    ph = next((p for p in phases if p.num == a.num), None)
    if not ph:
        raise SystemExit(f"no phase {a.num}")
    if a.action == "sign":
        unverified = [t.id for t in ph.tasks if t.status != "verified"]
        if unverified:
            raise SystemExit(f"cannot sign phase {a.num}: not verified → {', '.join(unverified)}")
        text = todo.read_text(encoding="utf-8")
        head = re.search(rf"^##\s+Phase\s+{a.num}\s*[—–-].*$", text, re.M)
        text = text[:head.end()] + f"\nsigned: {time.strftime('%Y-%m-%d')}" + text[head.end():]
        todo.write_text(text, encoding="utf-8")
        print(f"{name} phase {a.num} signed")
    return 0


def cmd_arch(a) -> int:
    from . import arch
    name = _project(a)
    docs = arch.docs(paths.PROJECTS / name / "arch")
    if not docs:
        raise SystemExit(f"{name} has no arch/*.md yet")
    if a.doc is None or a.doc == "--list":
        for d, p in docs.items():
            print(f"## {d}\n{arch.toc(p)}\n")
        return 0
    if a.doc not in docs:
        raise SystemExit(f"docs: {', '.join(docs)}")
    if a.list or not a.sections:
        print(arch.toc(docs[a.doc]))
    for s in a.sections:
        print(arch.section(docs[a.doc], s))
    return 0


def cmd_gate(a) -> int:
    from . import gate
    from . import project as projects
    return gate.run(projects.load(_project(a)), fast=a.fast, path=a.path)


def cmd_lesson(a) -> int:
    from . import trace
    name = _project(a)
    if a.action == "add":
        rec = trace.add_lesson(name, a.what, a.root_cause, a.rule, a.tags or [], a.severity, a.source)
        print(f"logged {rec['id']} · {rec['rule']}")
    elif a.action == "list":
        for l in trace.load_lessons(name):
            if a.all or l["status"] == "open":
                print(f"{l['id']} [{l['status']}] {l['date']} {l['severity']:<6} {l['what'][:70]}\n"
                      f"      rule: {l['rule']}")
    elif a.action == "status":
        trace.set_lesson_status(name, a.id, a.to)
        print(f"{a.id} → {a.to}")
    return 0


def cmd_mine(a) -> int:
    from . import mine
    print(mine.report(a.project, a.days, a.json, a.min_size))
    return 0


def cmd_eval(a) -> int:
    from pathlib import Path

    from . import evals
    if a.action == "run":
        return evals.run(a.project, a.split, a.label, Path(a.harness) if a.harness else None, a.trials, a.model)
    if a.action == "compare":
        return evals.compare_labels(a.base, a.cand)
    if a.action == "new":
        root = evals.new(a.project, a.id, a.prompt, a.verify, a.cluster or "")
        split = root.parent.name
        print(f"created eval {a.id} → {split}" + ("" if split == "heldin" else " (sealed — you won't see it again)"))
        if split == "heldin":
            print(f"  {root}  — put the starting files in fixture/")
        return 0
    if a.action == "list":
        for s in evals.SPLITS:
            ts = evals.tasks(a.project, s)
            print(f"{s}: {len(ts)} task(s)" + ("" if s == "heldout" else
                  "".join(f"\n  {t[1]['id']}  {t[1].get('cluster', '')}" for t in ts)))
        return 0
    return 2


def cmd_trash(a) -> int:
    from . import trash
    if a.action == "put":
        return trash.put(a.targets, a.cwd)
    if a.action == "list":
        return trash.list_()
    if a.action == "restore":
        return trash.restore(a.stamp)
    if a.action == "purge":
        return trash.purge(a.days)
    return 2


def cmd_new(a) -> int:
    from . import newproject
    root = newproject.create(a.name, a.repo or [], a.kind, a.description or "")
    print(f"created {root}")
    print("next: review project.toml (gate/format/lsp were detected, not guessed), then:")
    for h in newproject.lsp_hint(a.name):
        print("  " + h)
    return 0


def cmd_use(a) -> int:
    from . import project as projects
    projects.use(a.name)
    print(f"active project → {a.name}")
    return 0


def cmd_audit(a) -> int:
    from . import audit
    print(audit.report(a.days))
    return 0


def cmd_card(a) -> int:
    from . import project as projects
    from . import ui
    print(ui.card(a.project or projects.detect()))
    return 0


def cmd_statusline(a) -> int:
    from . import ui
    try:
        payload = json.load(sys.stdin)
    except Exception:
        payload = {}
    try:
        print(ui.statusline(payload))
    except Exception as e:  # never let the statusline crash the UI
        print(f"sage · statusline error: {e!r}"[:120])
    return 0


def cmd_hook(a) -> int:
    from . import hooks
    return hooks.dispatch(a.name)


def build() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="sagectl", description="sage — deterministic tooling")
    ap.add_argument("--version", action="version", version=__version__)
    sp = ap.add_subparsers(dest="cmd", required=True)

    def P(name, fn, help_):
        p = sp.add_parser(name, help=help_)
        p.set_defaults(fn=fn)
        return p

    p = P("where", cmd_where, "active phase card: tasks, waves, gate, lessons")
    p.add_argument("-p", "--project"); p.add_argument("--phase", type=int)
    p.add_argument("--all", action="store_true"); p.add_argument("--json", action="store_true")

    p = P("task", cmd_task, "set a task's status (verified is human-only)")
    p.add_argument("id"); p.add_argument("status"); p.add_argument("-p", "--project")

    p = P("phase", cmd_phase, "phase actions: sign (human-only)")
    p.add_argument("action", choices=["sign"]); p.add_argument("num", type=int); p.add_argument("-p", "--project")

    p = P("arch", cmd_arch, "read one section of a project's arch doc")
    p.add_argument("doc", nargs="?"); p.add_argument("sections", nargs="*")
    p.add_argument("--list", action="store_true"); p.add_argument("-p", "--project")

    p = P("gate", cmd_gate, "run the project's quality gate → one VERDICT line")
    p.add_argument("-p", "--project"); p.add_argument("--fast", action="store_true"); p.add_argument("--path")

    p = P("lesson", cmd_lesson, "log / list / close lessons (structured mistakes)")
    p.add_argument("action", choices=["add", "list", "status"]); p.add_argument("-p", "--project")
    p.add_argument("--what"); p.add_argument("--root-cause"); p.add_argument("--rule")
    p.add_argument("--tags", nargs="*"); p.add_argument("--severity", default="minor",
                                                        choices=["minor", "major", "critical"])
    p.add_argument("--source", default="manual"); p.add_argument("--all", action="store_true")
    p.add_argument("--id"); p.add_argument("--to", choices=["open", "graduated", "fixed", "wontfix"])

    p = P("mine", cmd_mine, "cluster failures into recurring mechanisms")
    p.add_argument("-p", "--project"); p.add_argument("--days", type=int, default=30)
    p.add_argument("--json", action="store_true"); p.add_argument("--min-size", type=int, default=1)

    p = P("eval", cmd_eval, "held-in/held-out evals: new · list · run · compare")
    p.add_argument("action", choices=["new", "list", "run", "compare"]); p.add_argument("-p", "--project")
    p.add_argument("--split", default="heldin"); p.add_argument("--label", default="current")
    p.add_argument("--harness"); p.add_argument("--trials", type=int, default=1); p.add_argument("--model")
    p.add_argument("--base"); p.add_argument("--cand")
    p.add_argument("--id"); p.add_argument("--prompt"); p.add_argument("--verify"); p.add_argument("--cluster")

    p = P("trash", cmd_trash, "reversible deletes: put · list · restore · purge")
    p.add_argument("action", choices=["put", "list", "restore", "purge"])
    p.add_argument("targets", nargs="*"); p.add_argument("--cwd"); p.add_argument("--stamp")
    p.add_argument("--days", type=int, default=14)

    p = P("new", cmd_new, "scaffold projects/<name> (stack-detected project.toml)")
    p.add_argument("name"); p.add_argument("--repo", action="append", help="name=path (repeatable)")
    p.add_argument("--kind", default="code"); p.add_argument("--description")

    p = P("use", cmd_use, "set the default active project"); p.add_argument("name")
    p = P("audit", cmd_audit, "context budget + unused skills/agents"); p.add_argument("--days", type=int, default=30)
    p = P("card", cmd_card, "print the session card"); p.add_argument("-p", "--project")
    P("statusline", cmd_statusline, "render the statusline (stdin: Claude Code JSON)")
    p = P("hook", cmd_hook, "hook entry point (stdin: hook JSON)"); p.add_argument("name")
    return ap


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if argv[:2] == ["trash", "put"] and "--" in argv:  # targets may start with '-'
        i = argv.index("--")
        head, targets = argv[:i], argv[i + 1:]
        a = build().parse_args(head)
        a.targets = targets
    else:
        a = build().parse_args(argv)
    return a.fn(a) or 0
