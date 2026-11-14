"""Salary range near pay words. Wraps providers._parse.parse_salary."""
from __future__ import annotations

import re

from ..providers._parse import parse_salary

_CODES = r"(?:CAD|USD|EUR|GBP|AUD|INR)"
_NUMB = r"(?:\d{1,3}(?:,\d{3})+|\d+(?:\.\d+)?)\s*[kK]?"
_SYM = r"(?:CA\$|C\$|US\$|A\$|[$€£₹])?"
_RANGE = re.compile(r"(?:" + _CODES + r"\s*)?" + _SYM + r"\s*" + _NUMB + r"\s*(?:-|to)\s*(?:" + _CODES + r"\s*)?" + _SYM + r"\s*" + _NUMB, re.I)
_PAY = re.compile(r"salary|compensation|pay range|pay scale|base pay|base salary|per (?:year|hour|annum)|annual|hourly|"
                  r"/\s*(?:yr|hr|year|hour)|range|remuneration|wage", re.I)


def extract(text: str, job: dict | None = None) -> dict:
    job = job or {}
    t = (text or "").replace("–", "-").replace("—", "-").replace("−", "-")
    # blank currency codes after digits so "100,000 CAD - $145,000 CAD" parses as a range (same length)
    spaced = re.sub(r"(?<=\d)(\s*)(" + _CODES + r")\b", lambda m: m.group(1) + " " * len(m.group(2)), t, flags=re.I)
    best = None
    for m in _RANGE.finditer(spaced):
        seg = spaced[m.start():m.end()]
        win_orig = t[max(0, m.start() - 80): m.end() + 60]
        hourly = bool(re.search(r"per hour|/\s*h(?:ou)?r|hourly|an hour", win_orig, re.I))
        has_money = bool(re.search(r"[$€£₹]|\b" + _CODES + r"\b|\d\s*[kK]\b", t[max(0, m.start() - 12): m.end() + 12], re.I))
        pay_word = bool(_PAY.search(win_orig))
        parsed = parse_salary(seg + " " + re.sub(r"\d", "", spaced[max(0, m.start() - 12):m.start()]) + spaced[m.end(): m.end() + 40])
        if not parsed:
            continue
        lo, hi = parsed["salary_min"], parsed["salary_max"]
        if not (hourly and lo >= 10) and lo < 1000:
            continue
        if not (has_money or pay_word):
            continue
        if re.search(r"\b(19|20)\d{2}\s*-\s*(19|20)\d{2}\b", seg):  # year ranges
            continue
        score = (2 if pay_word else 0) + (1 if has_money else 0)
        if best is None or score > best[0]:
            best = (score, parsed, win_orig)
    if not best:
        return {}
    _, p, win = best
    cur = ""
    mc = re.search(r"\b(" + _CODES + r")\b", win, re.I)
    if mc:
        cur = mc.group(1).upper()
    elif re.search(r"CA\$|C\$", win):
        cur = "CAD"
    elif re.search(r"US\$", win):
        cur = "USD"
    elif "€" in win:
        cur = "EUR"
    elif "£" in win:
        cur = "GBP"
    elif "$" in win and str(job.get("country", "")).upper() == "CA":
        cur = "CAD"
    out = {"salary_min": p["salary_min"], "salary_max": p["salary_max"]}
    if cur:
        out["currency"] = cur
    if p.get("salary_period"):
        out["salary_period"] = p["salary_period"]
    return out
