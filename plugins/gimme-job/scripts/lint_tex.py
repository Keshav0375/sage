#!/usr/bin/env python3
"""Resume style lint from knobs.resume.lint: tools per bullet, a number per bullet, line count, banned words.

  lint_tex.py FILE.tex [--json]    exit 1 on errors (warnings never fail)
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts import knobs as knobs_mod  # noqa: E402
from scripts.facts import tex_text  # noqa: E402
from scripts.rank import load_taxonomy  # noqa: E402


def bullets(tex: str) -> list[tuple[str, str]]:
    """(section, raw item) for every \\item inside experience/projects/summary."""
    body = tex.split("\\begin{document}", 1)[-1]
    body = re.sub(r"(?<!\\)%.*", "", body)
    out, section = [], ""
    for line in body.splitlines():
        m = re.search(r"\\begin\{rSection\}\{([^}]*)\}", line)
        if m:
            section = m.group(1)
        if re.search(r"\\item(?![a-z])", line) and section.lower() in ("experience", "projects", "professional summary"):
            out.append((section, re.split(r"\\item(?![a-z])", line, maxsplit=1)[1].strip()))
    return out


def lint(tex: str, cfg: dict) -> dict:
    tax = load_taxonomy()
    generic = {"llm", "llms", "rag", "agentic", "evals", "tracing", "containers", "observability", "machine learning"}
    tool_rx = [(a, re.compile(r"(?<![a-z0-9])" + re.escape(a) + r"(?![a-z0-9])")) for al in tax.values() for a in al
               if len(a) > 2 and a not in generic]
    errors, warnings = [], []
    for i, (sec, raw) in enumerate(bullets(tex), 1):
        txt = tex_text("\\begin{document}" + raw)
        tag = f"{sec} #{i}: {txt[:50]}…"
        low = txt.lower()
        tools = {a for a, rx in tool_rx if rx.search(low)}
        tools = {t for t in tools if not any(t != o and t in o for o in tools)}  # "kong" inside "kong ai gateway"
        if len(tools) > cfg["max_tools_per_bullet"] and sec.lower() != "professional summary":
            warnings.append(f"{tag} names {len(tools)} tools (max {cfg['max_tools_per_bullet']}): {', '.join(sorted(tools))}")
        if cfg["require_number"] and sec.lower() == "experience" and not re.search(r"\d", txt):
            warnings.append(f"{tag} has no number")
        lines = len(txt) / cfg["chars_per_line"]
        if lines > cfg["max_lines"] + 0.15:
            errors.append(f"{tag} runs ~{lines:.1f} lines (max {cfg['max_lines']})")
        for b in cfg["ban"]:
            if b in raw:
                errors.append(f"{tag} uses banned text {b!r}")
    return {"verdict": "FAIL" if errors else "PASS", "errors": errors, "warnings": warnings}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("file")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    k, _ = knobs_mod.load()
    res = lint(Path(a.file).read_text(encoding="utf-8"), k["resume"]["lint"])
    if a.json:
        print(json.dumps(res, indent=2))
    else:
        print(res["verdict"])
        for e in res["errors"]:
            print("  error", e)
        for w in res["warnings"]:
            print("  warn ", w)
    return 1 if res["errors"] else 0


if __name__ == "__main__":
    sys.exit(main())
