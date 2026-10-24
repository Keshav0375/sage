import importlib
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


@pytest.fixture
def home(tmp_path, monkeypatch):
    """An isolated SAGE_HOME with the real templates and one project, 'demo'."""
    import shutil

    shutil.copytree(ROOT / "_templates", tmp_path / "_templates")
    (tmp_path / "projects").mkdir()
    (tmp_path / ".claude" / "agents").mkdir(parents=True)
    (tmp_path / ".claude" / "agents" / "builder.md").write_text("---\nname: builder\n---\n")
    monkeypatch.setenv("SAGE_HOME", str(tmp_path))
    monkeypatch.delenv("SAGE_PROJECT", raising=False)
    for mod in [m for m in list(sys.modules) if m.startswith("sagectl")]:
        del sys.modules[mod]
    importlib.import_module("sagectl.paths")
    repo = tmp_path / "demo-repo"
    repo.mkdir()
    (repo / "pyproject.toml").write_text("[project]\nname='x'\n")
    from sagectl import newproject

    newproject.create("demo", [f"app={repo}"], "code", "test project")
    return tmp_path
