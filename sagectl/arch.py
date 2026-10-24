"""Section-addressed reader for a project's arch/*.md. Asking for one section costs a few hundred
tokens; Reading the whole doc to find it costs thousands. Offsets are computed per call, so
nothing goes stale when a doc is edited. Fence-aware: `#` comments in code blocks are not headings."""

from __future__ import annotations

import re
from pathlib import Path

NUM = re.compile(r"^(\d+(?:\.\d+)*)[.\s]")
HEAD = re.compile(r"^(#{1,6})\s+(.*)")


def headings(path: Path) -> list[dict]:
    lines = path.read_text(encoding="utf-8").split("\n")
    fence, raw = False, []
    for i, line in enumerate(lines):
        if line.lstrip().startswith("```"):
            fence = not fence
            continue
        if not fence and (m := HEAD.match(line)):
            raw.append((i + 1, len(m.group(1)), m.group(2).strip()))
    out = []
    for j, (start, level, title) in enumerate(raw):
        end = next((raw[k][0] - 1 for k in range(j + 1, len(raw)) if raw[k][1] <= level), len(lines))
        num = NUM.match(title)
        out.append({"start": start, "end": end, "level": level, "title": title,
                    "num": num.group(1) if num else None,
                    "text": "\n".join(lines[start - 1:end]).rstrip()})
    return out


def docs(arch_dir: Path) -> dict[str, Path]:
    return {p.stem.lower(): p for p in sorted(arch_dir.glob("*.md"))} if arch_dir.is_dir() else {}


def toc(path: Path) -> str:
    rows = []
    for h in headings(path):
        tok = len(h["text"]) // 4
        rows.append(f"{'  ' * (h['level'] - 1)}{h['title']}  (~{tok} tok)")
    return "\n".join(rows)


def section(path: Path, key: str) -> str:
    """By number (3.2), or by case-insensitive title substring / keyword (R6, auth)."""
    hs = headings(path)
    hit = [h for h in hs if h["num"] == key] or [h for h in hs if key.lower() in h["title"].lower()]
    if not hit:
        raise SystemExit(f"no section '{key}' in {path.name} — try --list")
    return "\n\n".join(h["text"] for h in hit)
