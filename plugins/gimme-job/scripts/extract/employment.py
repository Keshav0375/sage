"""Employment type and contract length."""
from __future__ import annotations

import re

from ..providers._parse import employment_from

_INTERN = re.compile(r"\b(?:internship|intern|co-?op|work term)\b", re.I)
_CONTRACT = re.compile(r"contract (?:position|role|opportunity|basis|duration|length|term)|fixed[- ]term|"
                       r"\d+[- ]?(?:month|mo)s?\.?\s+(?:fixed[- ]term\s+)?contract|contractor|term contract|"
                       r"(?:this|the) (?:is a |position is a |role is a )?contract\b|employment type\s*:\s*contract|\bcontract to hire\b|"
                       r"temporary contract|freelance", re.I)
_TEMP = re.compile(r"\btemporary\b|\bseasonal\b", re.I)
_PART = re.compile(r"part[- ]time", re.I)
_FULL = re.compile(r"full[- ]time|\bpermanent\b|\bregular position\b", re.I)
_MONTHS = re.compile(r"(\d{1,2})[- ]?(?:month|mo)s?\b|(\d{1,2})\s*months?\b|(\d)\s*(?:year|yr)s?[- ]?(?:contract|term)", re.I)


def extract(text: str, job: dict | None = None) -> dict:
    job = job or {}
    text = text or ""
    title = job.get("title") or ""
    e = employment_from(job.get("employment"))
    if not e:
        if _INTERN.search(title) or re.search(r"\b(?:this is an? |position is an? )?(?:internship|co-?op) (?:position|role|opportunity|term)", text, re.I):
            e = "intern"
        elif _CONTRACT.search(text) or _CONTRACT.search(title):
            e = "contract"
        elif _TEMP.search(text) and re.search(r"temporary (?:position|role|assignment|employment)", text, re.I):
            e = "temporary"
        elif _PART.search(text):
            e = "parttime"
        elif _FULL.search(text):
            e = "fulltime"
    if not e:
        return {}
    out: dict = {"employment": e}
    if e == "contract":
        for m in re.finditer(r"[^.\n]{0,80}\bcontract\b[^.\n]{0,80}|[^.\n]{0,60}\b(?:duration|term|length)\b[^.\n]{0,60}", text, re.I):
            mm = _MONTHS.search(m.group(0))
            if mm:
                n = mm.group(1) or mm.group(2)
                out["contract_months"] = int(n) if n else int(mm.group(3)) * 12
                break
    return out
