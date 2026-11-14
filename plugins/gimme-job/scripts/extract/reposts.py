"""Repost ('ghost job') detection: same fingerprint, new id, within N days."""
from __future__ import annotations

from datetime import date
from typing import Optional

from ._common import parse_date
from .fingerprint import fingerprint


def _when(j: dict, today: date) -> date:
    for k in ("posted_at", "first_seen", "seen_at"):
        d = parse_date(j.get(k))
        if d:
            return d
    return today


def detect_reposts(jobs: list[dict], history: list[dict], days: int = 90, today: Optional[date] = None) -> list[str]:
    today = today or date.today()
    past: dict[str, list[tuple[str, date]]] = {}
    for h in history or []:
        past.setdefault(h.get("fingerprint") or fingerprint(h), []).append((h.get("id", ""), _when(h, today)))
    flagged: list[str] = []
    for j in jobs or []:
        fp = j.get("fingerprint") or fingerprint(j)
        when = _when(j, today)
        for hid, hd in past.get(fp, []):
            if hid != j.get("id") and 0 <= (when - hd).days <= days:
                flagged.append(j.get("id", ""))
                break
    return flagged
