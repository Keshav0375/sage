"""Years of experience asked."""
from __future__ import annotations

import re

_W = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
      "twelve": 12, "fifteen": 15}
_N = r"(\d{1,2}|" + "|".join(_W) + r")(?:\s*\(\d{1,2}\))?"
_RANGE = re.compile(r"\b" + _N + r"\s*(\+)?\s*(?:-|to|–|—)\s*" + _N + r"\s*(\+)?\s*(?:years?|yrs?)\b", re.I)
_SINGLE = re.compile(r"\b(?:(at least|minimum(?: of)?|min\.?|over|more than)\s+)?" + _N + r"\s*(\+)?\s*(?:years?|yrs?)\b", re.I)
_EXP = re.compile(r"experience|exp\.|background|track record|hands-on|working with|developing|proven", re.I)
_EQUIV = re.compile(r"or equivalent|equivalent (?:work |practical |professional )?experience|or comparable|or related experience", re.I)
_SKIP = re.compile(r"years? (ago|old)|for (over |more than )?\d+ years|over \d+ years of (history|growth)|since \d{4}|\byears? of age", re.I)


def _n(v: str) -> int:
    return int(v) if v.isdigit() else _W[v.lower()]


def extract(text: str, job: dict | None = None) -> dict:
    text = text or ""
    mins: list[int] = []
    maxs: list[int] = []
    taken: list[tuple[int, int]] = []
    for m in _RANGE.finditer(text):
        ctx = text[max(0, m.start() - 70): m.end() + 70]
        if not _EXP.search(ctx) or _SKIP.search(text[m.start() - 15: m.end() + 5]):
            continue
        lo, hi = _n(m.group(1)), _n(m.group(3))
        if lo > hi or hi > 40:
            continue
        mins.append(lo)
        maxs.append(hi)
        taken.append((m.start(), m.end()))
    for m in _SINGLE.finditer(text):
        if any(a <= m.start() < b for a, b in taken):
            continue
        ctx = text[max(0, m.start() - 70): m.end() + 70]
        if not _EXP.search(ctx) or _SKIP.search(text[max(0, m.start() - 15): m.end() + 5]):
            continue
        n = _n(m.group(2))
        if n > 30:
            continue
        mins.append(n)
    if not mins:
        return {}
    out: dict = {"years_min": max(mins)}
    if maxs:
        out["years_max"] = max(maxs)
    if _EQUIV.search(text):
        out["or_equivalent"] = True
    return out
