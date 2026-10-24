"""`sagectl new` — scaffold projects/<name>/ from _templates/project, filling project.toml from
what is actually in the repos (stack → LSP, formatter, gate). Proposes; the human confirms."""

from __future__ import annotations

import shutil
from pathlib import Path

from . import paths
from . import project as projects

KINDS = ("code", "research", "qa")

LSP_PLUGINS = {  # server -> official marketplace plugin (verify with `/plugin` — names drift)
    "pyright": "pyright-lsp", "typescript": "typescript-lsp", "gopls": "gopls-lsp",
    "rust-analyzer": "rust-analyzer-lsp", "terraform-ls": "terraform-ls",
}


NO_REPOS = '# [[repos]]\n# name = "app"\n# path = "../app"     # relative to the sage root\n'


def _toml_list(xs: list[str]) -> str:
    return "[" + ", ".join(f'"{x}"' for x in xs) + "]"


def create(name: str, repos: list[str], kind: str = "code", description: str = "") -> Path:
    if kind not in KINDS:
        raise SystemExit(f"kind must be one of {KINDS}")
    root = paths.PROJECTS / name
    if root.exists():
        raise SystemExit(f"{root} already exists")
    shutil.copytree(paths.TEMPLATES / "project", root)

    stack = {"stacks": [], "lsp": [], "format": {}, "gate_full": [], "gate_fast": []}
    repo_blocks = []
    for spec in repos:
        rname, _, rpath = spec.partition("=") if "=" in spec else (Path(spec).name, "", spec)
        abs_path = (paths.SAGE_HOME / rpath).resolve() if not Path(rpath).is_absolute() else Path(rpath)
        found = projects.detect_stack(abs_path)
        for k in ("stacks", "lsp", "gate_full", "gate_fast"):
            stack[k] += [x for x in found[k] if x not in stack[k]]
        stack["format"].update(found["format"])
        repo_blocks.append(f'[[repos]]\nname = "{rname}"\npath = "{rpath}"\nbranch_from = "main"\npr_into = "main"\n')

    fmt = "\n".join(f'"{g}" = "{c}"' for g, c in stack["format"].items()) or '# "*.py" = "ruff format {file}"'
    first_repo = repos[0].partition("=")[0] if repos and "=" in repos[0] else (Path(repos[0]).name if repos else "")
    repos_toml = "".join(repo_blocks) or NO_REPOS
    toml = f'''name = "{name}"
kind = "{kind}"                     # code | research | qa
description = "{description}"
# detected stacks: {", ".join(stack["stacks"]) or "none"}

{repos_toml}
[gate]
repo = "{first_repo}"
full = {_toml_list(stack["gate_full"])}
fast = {_toml_list(stack["gate_fast"])}
stop_gate = false                  # true = Stop hook runs the fast gate on uncommitted changes

[format]
{fmt}

[lsp]
servers = {_toml_list(stack["lsp"])}

[guard]
dead_zones = []                    # paths no agent may read, e.g. ["archive/"]

[research]
subreddits = []                    # e.g. ["Python", "FastAPI"]
docs = []                          # library names for Context7, e.g. ["fastapi", "sqlalchemy"]
'''
    (root / "project.toml").write_text(toml, encoding="utf-8")
    for f in root.rglob("*.md"):
        f.write_text(f.read_text(encoding="utf-8").replace("{{PROJECT}}", name), encoding="utf-8")
    return root


def lsp_hint(name: str) -> list[str]:
    servers = projects.load(name).lsp
    return [f"/plugin install {LSP_PLUGINS.get(s, s)}@claude-plugins-official   # {s}" for s in servers]
