import json

TODO = """# Phases

## Phase 1 — Bootstrap
branch: dev/phase-1-bootstrap · repo: app
signed: 2026-10-01
- [verified] 1.1 Scaffold

## Phase 2 — Auth
branch: dev/phase-2-auth · repo: app · target: 2026-11-01
- [verified] 2.1 Models
- [wip] 2.2 Middleware · deps 2.1
- [todo] 2.3 Login API · deps 2.2
- [todo] 2.4 Docs
- [todo] 2.5 E2E · deps 2.3, 2.4, 1.1
"""


def test_parse_active_and_waves(home):
    from sagectl import tracker

    todo = home / "projects" / "demo" / "phases" / "TODO.md"
    todo.write_text(TODO)
    phases = tracker.parse(todo)
    assert [p.num for p in phases] == [1, 2]
    ph = tracker.active(phases)
    assert ph.num == 2 and ph.branch == "dev/phase-2-auth" and ph.meta["target"] == "2026-11-01"
    layers, cyc = tracker.waves(ph)
    assert layers == [["2.2", "2.4"], ["2.3"], ["2.5"]] and cyc == []


def test_cycle_is_reported_not_guessed(home):
    from sagectl import tracker

    todo = home / "projects" / "demo" / "phases" / "TODO.md"
    todo.write_text("## Phase 1 — X\n- [todo] 1.1 A · deps 1.2\n- [todo] 1.2 B · deps 1.1\n- [todo] 1.3 C\n")
    layers, cyc = tracker.waves(tracker.active(tracker.parse(todo)))
    assert layers == [["1.3"]] and cyc == ["1.1", "1.2"]


def test_set_status(home):
    from sagectl import tracker

    todo = home / "projects" / "demo" / "phases" / "TODO.md"
    todo.write_text(TODO)
    assert tracker.set_status(todo, "2.2", "review") == "wip"
    assert "- [review] 2.2 Middleware · deps 2.1" in todo.read_text()


def test_promotion_rule():
    from sagectl.evals import compare

    base = {"heldin": {"a": 0, "b": 1}, "heldout": {"x": 1, "y": 0}}
    better = {"heldin": {"a": 1, "b": 1}, "heldout": {"x": 1, "y": 0}}
    regress = {"heldin": {"a": 1, "b": 1}, "heldout": {"x": 0, "y": 1}}
    same = {"heldin": {"a": 0, "b": 1}, "heldout": {"x": 1, "y": 0}}
    assert compare(base, better)[0] == "PROMOTE"
    assert compare(base, regress)[0] == "REJECT"  # x passed before, fails now
    assert compare(base, same)[0] == "REJECT"
    assert compare({"heldin": {"a": 0}}, {"heldin": {"a": 1}})[0] == "REJECT"  # never promote blind


def test_split_is_deterministic_and_roughly_a_third():
    from sagectl.evals import assign_split

    ids = [f"t{i}" for i in range(300)]
    assert [assign_split(i) for i in ids] == [assign_split(i) for i in ids]
    held = sum(assign_split(i) == "heldout" for i in ids)
    assert 60 < held < 140


def test_mine_clusters_similar_failures(home):
    from sagectl import mine, trace

    for i in range(3):
        trace.add_lesson("demo", f"edited file {i} without reading it first", "skipped Read before Edit",
                         "always Read before Edit", ["edit"])
    trace.add_lesson("demo", "pushed with failing tests", "gate not run", "run gate before push", ["gate"])
    out = json.loads(mine.report("demo", as_json=True))
    assert out[0]["size"] == 3 and out[0]["kinds"] == ["lesson"]
    assert sum(c["size"] for c in out) == 4


def test_statusline_renders_without_git_or_cache(home):
    from sagectl import ui

    s = ui.statusline({"workspace": {"current_dir": str(home / "demo-repo")},
                       "context_window": {"used_percentage": 42}, "rate_limits": {"five_hour": {"used_percentage": 90}},
                       "cost": {"total_cost_usd": 1.5}})
    assert "sage" in s and "demo" in s and "42%" in s and "$1.50" in s


def test_new_project_detects_python_stack(home):
    from sagectl import project

    p = project.load("demo")
    assert "pyright" in p.lsp and "ruff check ." in p.gate["full"] and p.repos[0].name == "app"
    assert project.detect(home / "demo-repo" / "src") == "demo"
