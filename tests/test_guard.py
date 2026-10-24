from pathlib import Path


def bash(cmd, cwd="/tmp"):
    from sagectl import guard

    return guard.evaluate({"tool_name": "Bash", "tool_input": {"command": cmd}, "cwd": cwd})


def test_plain_rm_is_rewritten_to_trash(home):
    d = bash("rm -rf build dist", cwd=str(home))
    assert d.action == "rewrite"
    assert "trash put" in d.new_input["command"]
    assert "'build'" in d.new_input["command"] or " build" in d.new_input["command"]
    assert " rm " not in f" {d.new_input['command']} "


def test_rm_in_compound_command_is_denied(home):
    assert bash("cd x && rm -rf y").action == "deny"
    assert bash("ls | xargs rm").action == "deny"


def test_git_rm_is_not_treated_as_rm(home):
    assert bash("git rm --cached foo.txt").action == "allow"


def test_force_and_destructive_ops_denied(home):
    for cmd in ["git push --force origin main", "git push -f", "git reset --hard HEAD~1",
                "git branch -D feat", "git clean -fdx", "find . -name '*.pyc' -delete",
                "git push origin main --force-with-lease"]:
        assert bash(cmd).action == "deny", cmd


def test_normal_git_allowed(home):
    for cmd in ["git status", "git push -u origin main", "git commit -m 'feat: x'", "git restore --staged a"]:
        assert bash(cmd).action == "allow", cmd


def test_attribution_blocked(home):
    assert bash('git commit -m "x\n\nCo-Authored-By: Claude <noreply@anthropic.com>"').action == "deny"


def test_attribution_in_commit_file_blocked(home, tmp_path):
    f = tmp_path / "msg.txt"
    f.write_text("feat: y\n\nGenerated with Claude Code")
    assert bash(f"git commit -F {f}").action == "deny"


def test_verified_and_sign_are_human_only(home):
    assert bash("python3 bin/sagectl task 1.2 verified").action == "deny"
    assert bash("sagectl phase sign 1").action == "deny"
    assert bash("SAGE_HUMAN=1 sagectl task 1.2 review").action == "deny"
    assert bash("sagectl task 1.2 review").action == "allow"


def test_heldout_is_sealed(home):
    from sagectl import guard

    p = "/x/evals/harness/heldout/t1/task.toml"
    for tool in ("Read", "Edit", "Write"):
        assert guard.evaluate({"tool_name": tool, "tool_input": {"file_path": p}}).action == "deny"
    assert guard.evaluate({"tool_name": "Grep", "tool_input": {"path": "evals/harness/heldout"}}).action == "deny"
    assert bash("cat projects/demo/evals/heldout/x/task.toml").action == "deny"
    assert bash("sagectl eval run --split heldout --label base").action == "allow"
    heldin = {"tool_name": "Read", "tool_input": {"file_path": "/x/evals/harness/heldin/t/task.toml"}}
    assert guard.evaluate(heldin).action == "allow"


def test_secret_write_denied(home):
    from sagectl import guard

    d = guard.evaluate({"tool_name": "Write", "tool_input": {
        "file_path": "/tmp/a.py", "content": "KEY = 'ghp_" + "a" * 36 + "'"}})
    assert d.action == "deny"


def test_dead_zone_from_project_toml(home):
    from sagectl import guard

    toml = home / "projects" / "demo" / "project.toml"
    toml.write_text(toml.read_text().replace("dead_zones = []", 'dead_zones = ["archive/"]'))
    repo = str(home / "demo-repo")
    assert guard.evaluate({"tool_name": "Read", "tool_input": {"file_path": f"{repo}/archive/old.md"},
                           "cwd": repo}).action == "deny"
    assert bash("cat archive/old.md", cwd=repo).action == "deny"
    assert bash("cat src/new.md", cwd=repo).action == "allow"


def test_trash_put_and_restore_roundtrip(home):
    from sagectl import trash

    f = Path(home) / "demo-repo" / "junk.txt"
    f.write_text("keep me")
    trash.put([str(f)])
    assert not f.exists()
    stamp, items = trash.entries()[0]
    assert items[0]["from"] == str(f)
    trash.restore(stamp)
    assert f.read_text() == "keep me"
