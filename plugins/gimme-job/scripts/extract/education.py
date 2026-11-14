"""Degree asked and 'or equivalent experience' flag."""
from __future__ import annotations

import re

_LEVELS = [
    ("phd", r"ph\.?\s?d\b|doctorate|doctoral"),
    ("master", r"master(?:'|’)?s|\bm\.?sc\b|\bmba\b|\bm\.?eng\b|graduate degree|\bms\b"),
    ("bachelor", r"bachelor|\bb\.?sc\b|\bb\.?eng\b|\bb\.?a\b|undergraduate degree|university degree|college degree|"
                 r"post-?secondary|\bbs\b"),
]
_RANK = {"none": 0, "bachelor": 1, "master": 2, "phd": 3}
_NICE = re.compile(r"preferred|nice to have|\basset\b|a plus|bonus|desirable|advantage", re.I)
_EQUIV = re.compile(r"or equivalent|equivalent (?:work |practical |professional |industry )?experience|or comparable|"
                    r"or related (?:work )?experience|or relevant experience", re.I)
_NONE = re.compile(r"no degree (?:is )?required|degree (?:is )?not required|without a degree", re.I)


def extract(text: str, job: dict | None = None) -> dict:
    text = text or ""
    found: list[str] = []
    for sent in re.split(r"(?<=[.;!?])\s+|\n", text):
        if _NICE.search(sent) or _NONE.search(sent):
            continue
        s = sent.lower()
        lv = [name for name, pat in _LEVELS if re.search(pat, s)]
        if not lv and re.search(r"\bdegree in\b|\bdegree\b.{0,20}(?:required|related field)", s):
            lv = ["bachelor"]
        if lv and re.search(r"degree|bachelor|master|ph\.?d|doctor|diploma|education|\bb\.?sc|\bm\.?sc|\bmba", s):
            found.append(min(lv, key=lambda n: _RANK[n]))
    out: dict = {}
    if found:
        out["degree"] = min(found, key=lambda n: _RANK[n])
    elif _NONE.search(text):
        out["degree"] = "none"
    if out and _EQUIV.search(text):
        out["or_equivalent"] = True
    return out
