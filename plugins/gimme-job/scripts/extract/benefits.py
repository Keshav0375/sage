"""Benefit keywords, bonus, equity."""
from __future__ import annotations

import re

_BENEFITS = [
    ("health", r"health(?: care)?(?: insurance| benefits| coverage| and dental| & dental)|medical (?:insurance|coverage|benefits)|extended health"),
    ("dental", r"\bdental\b"),
    ("vision", r"\bvision (?:care|coverage|insurance|benefits)\b|\bvision\b(?=,| and| &)"),
    ("retirement", r"\brrsp\b|401\(?k\)?|pension|retirement (?:plan|savings)|\bdpsp\b"),
    ("vacation", r"vacation|paid time off|\bpto\b|paid holidays|annual leave"),
    ("parental_leave", r"parental leave|maternity|paternity|top-?up"),
    ("wellness", r"wellness|mental health|\beap\b|employee assistance"),
    ("learning", r"learning (?:budget|stipend|allowance)|professional development|training budget|tuition|education (?:budget|reimbursement)"),
    ("home_office", r"home[- ]office (?:stipend|allowance|budget|setup)|remote work stipend|work[- ]from[- ]home (?:stipend|allowance)"),
    ("flexible_hours", r"flexible (?:hours|schedule|working)|flex time"),
    ("life_insurance", r"life insurance|disability (?:insurance|coverage)|\bad&d\b"),
    ("stock", r"stock options?|equity|\brsus?\b|\bespp\b|employee share|share purchase|stock purchase"),
    ("bonus", r"(?:annual|performance|signing|sign-on|discretionary|target|incentive|referral|retention) bonus|bonus (?:plan|program|eligib\w*|target)|variable (?:pay|compensation)|incentive (?:plan|pay|compensation)"),
]


def extract(text: str, job: dict | None = None) -> dict:
    low = (text or "").lower()
    found = [name for name, pat in _BENEFITS if re.search(pat, low)]
    out: dict = {}
    if found:
        out["benefits"] = found
    if "bonus" in found:
        out["bonus"] = True
    if "stock" in found:
        out["equity"] = True
    return out
