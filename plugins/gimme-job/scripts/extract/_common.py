"""Shared helpers for field extractors (rule-based, stdlib only)."""
from __future__ import annotations

import re
from datetime import date, datetime
from typing import Optional

MONTHS = {m: i + 1 for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"])}
_MON = r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|June?|July?|Aug(?:ust)?|Sept?(?:ember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"
DATE_RE = (
    r"(?:(?P<mon>" + _MON + r")\.?\s+(?P<d>\d{1,2})(?:st|nd|rd|th)?(?:,?\s*(?P<y>\d{4}))?"
    r"|(?P<d2>\d{1,2})(?:st|nd|rd|th)?\s+(?:of\s+)?(?P<mon2>" + _MON + r")\.?,?(?:\s+(?P<y2>\d{4}))?"
    r"|(?P<iso>\d{4}-\d{2}-\d{2}))"
)


def date_from_match(m: re.Match, today: Optional[date] = None) -> Optional[date]:
    today = today or date.today()
    try:
        if m.group("iso"):
            return date.fromisoformat(m.group("iso"))
        if m.group("mon"):
            mon, d, y = m.group("mon"), m.group("d"), m.group("y")
        else:
            mon, d, y = m.group("mon2"), m.group("d2"), m.group("y2")
        mo = MONTHS[mon[:3].lower()]
        if y:
            return date(int(y), mo, int(d))
        cand = date(today.year, mo, int(d))
        if (today - cand).days > 60:
            cand = date(today.year + 1, mo, int(d))
        return cand
    except (ValueError, KeyError):
        return None


def parse_date(value) -> Optional[date]:
    """date from ISO-ish string / datetime / date, or None."""
    if not value:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    s = str(value).strip()
    try:
        return date.fromisoformat(s[:10])
    except ValueError:
        pass
    m = re.search(DATE_RE, s)
    return date_from_match(m) if m else None


def lines(text: str) -> list[str]:
    return [ln.strip() for ln in (text or "").splitlines() if ln.strip()]
