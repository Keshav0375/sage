"""Sponsorship, security clearance, citizenship rules."""
from __future__ import annotations

import re

_NOT = re.compile(
    r"(?:does|do|will|would|can|could)\s*(?:not|n(?:'|’)t)\s+(?:\w+\s+){0,3}?(?:provide|offer|support|consider)?\s*(?:\w+\s+){0,3}?(?:sponsorship|sponsor)|"
    r"(?:unable|not able|cannot|can(?:'|’)t|won(?:'|’)t)\s+(?:to\s+)?(?:\w+\s+){0,3}?(?:sponsor|provide sponsorship|offer sponsorship)|"
    r"no\s+(?:visa\s+|immigration\s+)?sponsorship|sponsorship\s+(?:is\s+)?not\s+(?:available|offered|provided)|"
    r"without\s+(?:the need for\s+)?(?:visa\s+|employer\s+)?sponsorship|"
    r"not\s+(?:now\s+)?(?:or\s+in\s+the\s+future\s+)?require\s+(?:visa\s+)?sponsorship|"
    r"not\s+(?:able|in a position)\s+to\s+(?:offer|provide)\s+(?:\w+\s+)?(?:visa|immigration)", re.I)
_YES = re.compile(
    r"(?:visa|immigration|work permit)\s+sponsorship\s+(?:is\s+|may be\s+)?(?:available|provided|offered|possible)|"
    r"(?:we|company)\s+(?:will\s+|can\s+|do\s+|does\s+)?(?:offer\s+|provide\s+)?(?:visa\s+)?sponsor(?:ship)?\s*(?:visas?|candidates|work)|"
    r"sponsorship\s+(?:available|offered|provided)|(?:will|can|do|does)\s+sponsor\b|"
    r"relocation\s+(?:and|&)\s+visa|(?:offers?|provides?)\s+(?:visa|immigration)\s+(?:sponsorship|support|assistance)", re.I)
_CLEAR = [
    (r"enhanced reliability", "Enhanced Reliability Status"),
    (r"reliability status", "Reliability Status"),
    (r"top[- ]secret|\bTS/SCI\b", "Top Secret"),
    (r"secret (?:security )?clearance|\bsecret level\b|level ii security|\bsecret\b clearance", "Secret"),
    (r"public trust", "Public Trust"),
    (r"security clearance", "Security Clearance"),
]
_CIT = re.compile(r"must be (?:a |an )?(?:canadian|u\.?s\.?|american|british|eu)\s+citizen|citizenship\s+(?:is\s+)?(?:required|mandatory)|"
                  r"(?:canadian|u\.?s\.?)\s+citizenship\s+(?:is\s+)?(?:required|mandatory)|"
                  r"only\s+(?:canadian|u\.?s\.?)\s+citizens", re.I)


def extract(text: str, job: dict | None = None) -> dict:
    text = text or ""
    out: dict = {}
    if _NOT.search(text):
        out["sponsorship"] = "not_offered"
    elif _YES.search(text):
        out["sponsorship"] = "offered"
    for pat, name in _CLEAR:
        if re.search(pat, text, re.I):
            out["clearance"] = name
            break
    if _CIT.search(text):
        out["citizenship_required"] = True
    return out
