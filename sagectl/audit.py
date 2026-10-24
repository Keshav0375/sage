"""Context budget + bloat audit. Every session pays for CLAUDE.md, imported skills, skill and
agent descriptions and the output style on every turn. One Reddit audit found 45K tokens loaded
before the first prompt. sage's budget is 15K; this measures it (chars/4 estimate — run
`/context` in a live session for the exact number) and flags what nobody uses."""

from __future__ import annotations

import re
from pathlib import Path

from . import paths, trace

BUDGET = 15_000
FRONT = re.compile(r"^---\n(.*?)\n---", re.S)


def _tok(text: str) -> int:
    return len(text) // 4


def _desc(md: Path) -> str:
    m = FRONT.match(md.read_text(encoding="utf-8"))
    if not m:
        return ""
    d = re.search(r"^description:\s*(.+)$", m.group(1), re.M)
    return d.group(1) if d else ""


def measure() -> list[tuple[str, int]]:
    rows = []
    home = paths.SAGE_HOME
    claude_md = home / "CLAUDE.md"
    if claude_md.is_file():
        text = claude_md.read_text(encoding="utf-8")
        rows.append(("CLAUDE.md", _tok(text)))
        for imp in re.findall(r"^@(\S+)", text, re.M):
            p = home / imp
            if p.is_file():
                rows.append((f"@{imp}", _tok(p.read_text(encoding="utf-8"))))
    skills = sorted((home / ".claude" / "skills").glob("*/SKILL.md"))
    rows.append((f"skill descriptions ×{len(skills)}", sum(_tok(_desc(s)) + 10 for s in skills)))
    agents = sorted((home / ".claude" / "agents").glob("*.md"))
    rows.append((f"agent descriptions ×{len(agents)}", sum(_tok(_desc(a)) + 10 for a in agents)))
    for style in (home / ".claude" / "output-styles").glob("*.md"):
        rows.append((f"output style {style.stem}", _tok(style.read_text(encoding="utf-8"))))
    return rows


def unused(days: int = 30) -> tuple[list[str], list[str]]:
    used = {(r.get("tool"), r.get("name")) for r in trace.read(days=days, event="use")}
    skills = [s.parent.name for s in (paths.SAGE_HOME / ".claude" / "skills").glob("*/SKILL.md")]
    agents = [a.stem for a in (paths.SAGE_HOME / ".claude" / "agents").glob("*.md")]
    return ([s for s in skills if ("Skill", s) not in used and s != "ground-rules"],
            [a for a in agents if ("Agent", a) not in used])


def report(days: int = 30) -> str:
    rows = measure()
    total = sum(n for _, n in rows)
    lines = [f"{name:<34} ~{n:>6,} tok" for name, n in rows]
    flag = "OK" if total <= BUDGET else "OVER"
    lines.append(f"{'TOTAL (sage-owned, est.)':<34} ~{total:>6,} tok · budget {BUDGET:,} · {flag}")
    lines.append("  + Claude Code's own system prompt & tool schemas — check `/context` live.")
    has_traces = bool(trace.read(days=days, event="use"))
    if has_traces:
        s, a = unused(days)
        lines.append(f"unused {days}d — skills: {', '.join(s) or 'none'}")
        lines.append(f"unused {days}d — agents: {', '.join(a) or 'none'}")
    else:
        lines.append("usage: no traces yet — unused-item check needs a few sessions of data.")
    return "\n".join(lines)
