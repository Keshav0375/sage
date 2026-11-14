#!/usr/bin/env python3
"""Fact bank + automatic fact gate (replaces human approval).

facts.json: {"skills": [...], "locked": {"titles": [...], "employers": [...], "dates": [...]},
             "facts": [{"id", "claim", "metrics": ["48%", ...], "section", "source", "proof"}]}

  facts.py check FILE.tex [--parent FILE.tex] [--json]   gate: exit 1 on BLOCK
  facts.py list
  facts.py seed FILE.tex                                   print fact candidates from a resume (numbers + bullets)

Gate rules (plan section 5):
  BLOCK  a number in the new resume that is not in any fact's metrics (or in the parent resume when --parent is given
         and that number is also in facts)
  BLOCK  a locked title / employer / date from facts.json missing from the new resume
  BLOCK  rounding up: a number close to a fact number but larger (48% → 50%)
  WARN   a skill named in the resume that is not in facts.skills
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts import common  # noqa: E402
from scripts import knobs as knobs_mod  # noqa: E402

NUM = re.compile(r"(?<![\w.])(?:~|\\\$|\$)?\d[\d,]*(?:\.\d+)?\s*(?:\\%|%|x|K|k|M|ms|s|min|\+)?(?![\w])")
LATEX_CMD = re.compile(r"\\(?:href)\{[^}]*\}|\\[a-zA-Z]+\*?(?:\[[^\]]*\])?")


def tex_text(tex: str) -> str:
    """Rough LaTeX → text: drop preamble, comments, commands; keep visible words."""
    body = tex.split("\\begin{document}", 1)[-1]
    body = re.sub(r"(?<!\\)%.*", "", body)
    body = re.sub(r"\\ats\{([^}]*)\}\{[^}]*\}", r"\1", body)
    body = re.sub(r"\\href\{[^}]*\}\{([^}]*)\}", r"\1", body)
    body = re.sub(r"\\(?:begin|end)\{[^}]*\}(?:\[[^\]]*\])?(?:\{[^}]*\})?", " ", body)
    body = re.sub(r"\\(?:itemsep|vspace|hspace|setlength)\b[^\n]*?(?=\\item|$)", " ", body, flags=re.M)
    body = re.sub(r"\[[a-z]+=[^\]]*\]", " ", body)
    body = body.replace("\\%", "%").replace("\\&", "&").replace("\\$", "$").replace("\\#", "#").replace("$\\sim$", "~")
    body = re.sub(r"\\textasciitilde\{?\}?", "~", body)
    body = LATEX_CMD.sub(" ", body)
    body = re.sub(r"[{}]", " ", body)
    return re.sub(r"\s+", " ", body).strip()


def norm_num(s: str) -> str:
    s = s.replace("\\", "").replace(",", "").replace(" ", "").replace("~", "").replace("$", "").lower()
    return s


def numbers(text: str) -> set[str]:
    out = set()
    for m in NUM.finditer(text):
        n = norm_num(m.group(0))
        core = re.match(r"\d+(?:\.\d+)?", n)
        if not core:
            continue
        val = float(core.group(0))
        raw = m.group(0)
        if 1990 <= val <= 2100 and re.fullmatch(r"\d{4}", raw.strip()):   # years in dates are checked as locked dates
            continue
        out.add(n)
    return out


def _value(n: str) -> float:
    m = re.match(r"\d+(?:\.\d+)?", n)
    v = float(m.group(0)) if m else 0.0
    return v * 1000 if n.endswith("k") else v


def load_facts(k: dict) -> dict:
    return common.read_json(common.data_root(k) / "facts.json", {}) or {"skills": [], "locked": {}, "facts": []}


def check(tex: str, facts: dict, parent_tex: str | None = None) -> dict:
    text = tex_text(tex)
    allowed = set()
    for f in facts.get("facts", []):
        for m in f.get("metrics", []):
            allowed.add(norm_num(m))
        allowed |= numbers(f.get("claim", ""))
    allowed |= {norm_num(x) for x in facts.get("allowed_numbers", [])}
    found = numbers(text)
    blocks, warns = [], []
    for n in sorted(found - allowed):
        bigger = [a for a in allowed if a and a[-1:] == n[-1:] and 0 < _value(a) < _value(n) <= _value(a) * 1.15]
        if bigger:
            blocks.append(f"rounded up: '{n}' vs fact '{bigger[0]}'")
        else:
            blocks.append(f"number with no fact: '{n}'")
    low = text.lower()
    for kind in ("titles", "employers", "dates"):
        for item in facts.get("locked", {}).get(kind, []):
            if item.lower() not in low:
                blocks.append(f"locked {kind[:-1]} missing or changed: '{item}'")
    sk = {s.lower() for s in facts.get("skills", [])}
    if sk:
        from scripts.rank import load_taxonomy, skills_in
        tax = load_taxonomy()
        known = " ".join(facts.get("skills", [])) + " " + " ".join(f.get("claim", "") for f in facts.get("facts", []))
        sk |= {s.lower() for s in skills_in(known, tax)}
        for s in sorted(skills_in(text, load_taxonomy())):
            if s.lower() not in sk:
                warns.append(f"skill not in facts.skills: {s}")
    return {"verdict": "BLOCK" if blocks else "PASS", "blocks": blocks, "warnings": warns, "numbers_checked": len(found)}


def seed(tex: str) -> list[dict]:
    text = tex_text(tex)
    items = re.split(r"\\item", tex.split("\\begin{document}", 1)[-1])
    out = []
    n = 0
    for it in items[1:]:
        it = re.split(r"\\end\{itemize\}|\\textbf\{|\\newpage|\\begin\{rSection\}", it)[0]
        t = tex_text("\\begin{document}" + it)[:400]
        if len(t) < 25:
            continue
        n += 1
        i = n
        nums = sorted(numbers(t))
        if t:
            out.append({"id": f"F{i:03d}", "claim": t, "metrics": nums, "section": "", "source": "resume v1", "proof": ""})
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["check", "list", "seed"])
    ap.add_argument("file", nargs="?")
    ap.add_argument("--parent")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    k, _ = knobs_mod.load()
    if a.cmd == "list":
        for f in load_facts(k).get("facts", []):
            print(f"{f['id']}: {f['claim'][:100]}  {f.get('metrics', [])}")
        return 0
    tex = Path(a.file).read_text(encoding="utf-8")
    if a.cmd == "seed":
        print(json.dumps(seed(tex), indent=2, ensure_ascii=False))
        return 0
    res = check(tex, load_facts(k), Path(a.parent).read_text(encoding="utf-8") if a.parent else None)
    if a.json:
        print(json.dumps(res, indent=2))
    else:
        print(res["verdict"])
        for b in res["blocks"]:
            print("  BLOCK", b)
        for w in res["warnings"]:
            print("  warn ", w)
    return 1 if res["verdict"] == "BLOCK" else 0


if __name__ == "__main__":
    sys.exit(main())
