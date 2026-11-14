"""Posted / closing dates from phrases."""
from __future__ import annotations

import re
from datetime import date, timedelta
from typing import Optional

from ._common import DATE_RE, date_from_match
from ..providers._parse import to_iso

_CLOSE = re.compile(
    r"(?:closing\s+date|close\s+date|closes?(?:\s+on)?|application\s+deadline|deadline(?:\s+to\s+apply)?|"
    r"apply\s+(?:by|before)|applications?\s+(?:are\s+)?(?:will\s+be\s+)?(?:accepted\s+)?(?:until|through|up to)|open\s+until|"
    r"posting\s+closes?)\b\s*(?:is|on|by)?\s*[:\-]?\s*(?:on\s+)?" + DATE_RE, re.I)
_POSTED = re.compile(
    r"(?:date\s+posted|posted(?:\s+on)?|posting\s+date|published(?:\s+on)?|date\s+published|open\s+date)\s*[:\-]?\s*(?:on\s+)?" + DATE_RE, re.I)
_REL = re.compile(r"posted\s+(?:(\d+)\s+(day|week|month)s?\s+ago|(today|yesterday))", re.I)


def extract(text: str, job: dict | None = None, today: Optional[date] = None) -> dict:
    job = job or {}
    text = text or ""
    today = today or date.today()
    out: dict = {}
    if job.get("posted_at"):
        out["posted_at"] = to_iso(job["posted_at"]) or str(job["posted_at"])
    if job.get("closes_at"):
        out["closes_at"] = to_iso(job["closes_at"]) or str(job["closes_at"])
    if "closes_at" not in out:
        m = _CLOSE.search(text)
        if m:
            d = date_from_match(m, today)
            if d:
                out["closes_at"] = d.isoformat()
    if "posted_at" not in out:
        m = _POSTED.search(text)
        if m:
            d = date_from_match(m, today)
            if d:
                out["posted_at"] = d.isoformat()
        else:
            r = _REL.search(text)
            if r:
                if r.group(3):
                    d = today - timedelta(days=1 if r.group(3).lower() == "yesterday" else 0)
                else:
                    mult = {"day": 1, "week": 7, "month": 30}[r.group(2).lower()]
                    d = today - timedelta(days=int(r.group(1)) * mult)
                out["posted_at"] = d.isoformat()
    return out
