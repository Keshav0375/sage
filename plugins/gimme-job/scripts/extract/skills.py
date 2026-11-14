"""Skills from the shared taxonomy, split into required vs nice-to-have."""
from __future__ import annotations

import re
import tomllib
from functools import lru_cache
from pathlib import Path

TAXONOMY = Path(__file__).resolve().parent.parent.parent / "config" / "skills-taxonomy.toml"
_AMBIGUOUS_BLOCK = {"go": r"(?!\s+(?:to|beyond|above|the|ahead|live|from|forward|with|and\s+get))"}


@lru_cache(maxsize=1)
def _compiled() -> list[tuple[str, re.Pattern]]:
    with open(TAXONOMY, "rb") as f:
        data = tomllib.load(f)
    out = []
    for entry in data.get("skills", {}).values():
        name = entry["name"]
        pats = []
        for alias in sorted(set([name] + list(entry.get("aliases", []))), key=len, reverse=True):
            a = alias.lower()
            body = re.escape(a)
            lb, la = r"(?<![\w+#.\-])", r"(?![\w+#])"
            if a.startswith("."):
                lb = r"(?<![\w])"
            if a.isalpha() and len(a) <= 4 and a not in ("java", "rust", "lua", "rag", "bash", "node", "scala", "ruby", "perl", "dart", "kafka", "spark", "sql", "aws", "gcp", "llm", "api"):
                # short, collides with English: only Capitalised or UPPER form, never lowercase
                forms = {a.capitalize(), a.upper()}
                pat = r"(?:" + "|".join(re.escape(x) for x in forms) + r")" + _AMBIGUOUS_BLOCK.get(a, "")
                pats.append(("cs", lb + pat + la))
            else:
                pats.append(("ci", lb + body + la))
        ci = "|".join(p for k, p in pats if k == "ci")
        cs = "|".join(p for k, p in pats if k == "cs")
        out.append((name, re.compile(ci, re.I) if ci else None, re.compile(cs) if cs else None))
    return out


def find_skills(text: str) -> list[str]:
    hits = []
    for name, ci, cs in _compiled():
        pos = []
        for rx in (ci, cs):
            if rx:
                m = rx.search(text)
                if m:
                    pos.append(m.start())
        if pos:
            hits.append((min(pos), name))
    return [n for _, n in sorted(hits)]


_NICE = re.compile(r"nice[- ]to[- ]have|preferred|bonus|\basset\b|\bassets\b|is a plus|are a plus|would be a plus|"
                   r"good to have|desirable|beneficial|an advantage|a plus\b|extra credit|great to have", re.I)
_REQ = re.compile(r"requirements?|qualifications?|must[- ]have|what you(?:'|’)?ll (?:need|bring)|responsibilit|"
                  r"what we(?:'|’)?re looking for|about the role|what you(?:'|’)?ll do|your profile|skills|key duties|essential", re.I)


def split_sections(text: str) -> tuple[str, str]:
    req, nice = [], []
    mode = "req"
    for ln in (text or "").splitlines():
        s = ln.strip()
        if not s:
            continue
        headingish = len(s) <= 70 and not re.search(r"[.;]$", s) and not s.startswith(("-", "•", "*"))
        if headingish and _NICE.search(s):
            mode = "nice"
            continue
        if headingish and _REQ.search(s):
            mode = "req"
            continue
        if _NICE.search(s) and not headingish:
            nice.append(s)          # inline "...is a plus" sentences
            continue
        (req if mode == "req" else nice).append(s)
    return "\n".join(req), "\n".join(nice)


def extract(text: str, job: dict | None = None) -> dict:
    req_text, nice_text = split_sections(text or "")
    required = find_skills(req_text)
    nice = [s for s in find_skills(nice_text) if s not in required]
    out: dict = {}
    if required:
        out["required"] = required
    if nice:
        out["nice_to_have"] = nice
    return out
