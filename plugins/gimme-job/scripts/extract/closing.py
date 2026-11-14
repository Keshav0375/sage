"""Jobs closing within N days."""
from __future__ import annotations

from datetime import date, timedelta
from typing import Optional

from ._common import parse_date


def closing_soon(jobs: list[dict], days: int = 7, today: Optional[date] = None) -> list[str]:
    today = today or date.today()
    end = today + timedelta(days=days)
    out = []
    for j in jobs or []:
        d = parse_date(j.get("closes_at"))
        if d and today <= d <= end:
            out.append(j.get("id", ""))
    return out
