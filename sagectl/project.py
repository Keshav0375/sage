"""Projects: one folder under projects/, described by project.toml. Nothing project-specific
lives in code — the gate, formatter, LSP servers, dead zones and research sources all come
from the project's own config, so one harness serves every project."""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from . import paths


@dataclass
class Repo:
    name: str
    path: Path
    branch_from: str = "main"
    pr_into: str = "main"


@dataclass
class Project:
    name: str
    root: Path
    kind: str = "code"
    description: str = ""
    repos: list[Repo] = field(default_factory=list)
    gate: dict = field(default_factory=dict)
    format: dict = field(default_factory=dict)
    lsp: list[str] = field(default_factory=list)
    dead_zones: list[str] = field(default_factory=list)
    research: dict = field(default_factory=dict)
    raw: dict = field(default_factory=dict)

    def repo(self, name: str | None = None) -> Repo | None:
        if not self.repos:
            return None
        if name is None:
            return self.repos[0]
        return next((r for r in self.repos if r.name == name), None)


def load(name: str) -> Project:
    root = paths.PROJECTS / name
    cfg = root / "project.toml"
    if not cfg.is_file():
        raise SystemExit(f"no project '{name}' (expected {cfg})")
    data = tomllib.loads(cfg.read_text(encoding="utf-8"))
    repos = [
        Repo(
            name=r["name"],
            path=(paths.SAGE_HOME / r["path"]).resolve() if not Path(r["path"]).is_absolute() else Path(r["path"]),
            branch_from=r.get("branch_from", "main"),
            pr_into=r.get("pr_into", r.get("branch_from", "main")),
        )
        for r in data.get("repos", [])
    ]
    return Project(
        name=data.get("name", name),
        root=root,
        kind=data.get("kind", "code"),
        description=data.get("description", ""),
        repos=repos,
        gate=data.get("gate", {}),
        format=data.get("format", {}),
        lsp=data.get("lsp", {}).get("servers", []),
        dead_zones=data.get("guard", {}).get("dead_zones", []),
        research=data.get("research", {}),
        raw=data,
    )


def names() -> list[str]:
    if not paths.PROJECTS.is_dir():
        return []
    return sorted(p.name for p in paths.PROJECTS.iterdir() if (p / "project.toml").is_file())


def detect(cwd: str | Path | None = None) -> str | None:
    """The project a working directory belongs to: inside projects/<name>/, inside one of a
    project's repos, then $SAGE_PROJECT, then the last `sagectl use` choice."""
    here = Path(cwd or os.getcwd()).resolve()
    try:
        rel = here.relative_to(paths.PROJECTS.resolve())
        if rel.parts and (paths.PROJECTS / rel.parts[0] / "project.toml").is_file():
            return rel.parts[0]
    except ValueError:
        pass
    for name in names():
        try:
            proj = load(name)
        except Exception:  # a broken project.toml must not break every hook
            continue
        for r in proj.repos:
            if here == r.path or r.path in here.parents:
                return name
    env = os.environ.get("SAGE_PROJECT")
    if env and env in names():
        return env
    active = paths.RUNTIME / "active"
    if active.is_file():
        val = active.read_text().strip()
        if val in names():
            return val
    return None


def use(name: str) -> None:
    load(name)
    paths.ensure(paths.RUNTIME)
    (paths.RUNTIME / "active").write_text(name + "\n")


# --- stack detection: what /new-project proposes for a repo --------------------------------

STACKS = [
    # marker file, stack, lsp server, formatter (glob -> cmd), full gate, fast gate
    ("pyproject.toml", "python", "pyright", {"*.py": "ruff format {file}"},
     ["ruff check .", "pyright", "pytest -q"], ["ruff check ."]),
    ("package.json", "typescript", "typescript", {"*.{ts,tsx,js,jsx}": "npx prettier --write {file}"},
     ["npm run -s lint", "npx tsc --noEmit", "npm test --silent"], ["npm run -s lint"]),
    ("go.mod", "go", "gopls", {"*.go": "gofmt -w {file}"},
     ["go vet ./...", "go test ./..."], ["go vet ./..."]),
    ("Cargo.toml", "rust", "rust-analyzer", {"*.rs": "rustfmt {file}"},
     ["cargo clippy -q", "cargo test -q"], ["cargo check -q"]),
    ("main.tf", "terraform", "terraform-ls", {"*.tf": "terraform fmt {file}"},
     ["terraform fmt -check -recursive", "terraform validate", "tflint"], ["terraform fmt -check -recursive"]),
]


def detect_stack(repo: Path) -> dict:
    found = {"stacks": [], "lsp": [], "format": {}, "gate_full": [], "gate_fast": []}
    if not repo.is_dir():
        return found
    for marker, stack, lsp, fmt, full, fast in STACKS:
        hit = (repo / marker).exists() or (marker.endswith(".tf") and any(repo.glob("**/*.tf")))
        if hit:
            found["stacks"].append(stack)
            found["lsp"].append(lsp)
            found["format"].update(fmt)
            found["gate_full"] += full
            found["gate_fast"] += fast
    return found
