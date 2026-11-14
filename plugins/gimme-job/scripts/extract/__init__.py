"""Rule-based job-page extraction. Rules first; fall back to the Haiku extract-worker when confidence is low."""
from __future__ import annotations

from . import (benefits, company, contacts, dates, education, employment, location, salary, skills, title, work_auth,
               years)

EXTRACTORS = (title, location, salary, years, skills, education, work_auth, employment, dates, contacts, benefits, company)

KEY_FIELDS = ("level", "family", "country", "workplace", "salary_min", "years_min", "required", "degree", "employment")


def extract_all(text: str, job: dict | None = None) -> dict:
    out: dict = {}
    for mod in EXTRACTORS:
        try:
            res = mod.extract(text, job)
        except Exception:        # one bad rule must not sink the rest
            continue
        for k, v in res.items():
            if v not in (None, "", [], {}):
                out.setdefault(k, v)
    return out


def rules_confidence(fields: dict) -> float:
    found = sum(1 for k in KEY_FIELDS if fields.get(k) not in (None, "", [], {}))
    return found / len(KEY_FIELDS)
