"""Remotli (Swiss remote jobs) — public JSON API, board-wide.

GET https://remotli.ch/api/jobs?page=N&limit=50&remote=all
Mechanism from career-ops providers/remotli.mjs (MIT); code is our own.
"""
from __future__ import annotations

import re
from urllib.parse import urlsplit

from ._base import Context, Job, Provider, ProviderError, Target
from ._parse import html_to_text, to_iso

ORIGIN = "https://remotli.ch"
PAGE = 50


def _num(v):
    try:
        n = float(v)
    except (TypeError, ValueError):
        return None
    return n if n >= 0 else None


class Remotli(Provider):
    name = "remotli"
    wave = "W5"
    kind = "board"
    tenant = False
    hosts = ("remotli.ch",)

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        max_pages = int(target.options.get("max_pages") or 20)
        jobs: list[Job] = []
        total_pages, page = 1, 1
        while page <= min(max_pages, total_pages):
            try:
                data = ctx.http.get_json(f"{ORIGIN}/api/jobs?page={page}&limit={PAGE}&remote=all")
                if not isinstance(data, dict) or not isinstance(data.get("jobs"), list):
                    raise ProviderError("remotli: unexpected response, expected {jobs: [...]}")
            except ProviderError:
                if not jobs:
                    raise
                break
            rows = data["jobs"]
            tp = (data.get("pagination") or {}).get("totalPages")
            if isinstance(tp, int) and tp > 0:
                total_pages = tp
            for row in rows:
                j = (row or {}).get("jobs") or {}
                title = (j.get("title") or "").strip()
                if not title or str(j.get("status") or "").strip().lower() != "active":
                    continue
                slug = (j.get("slug") or "").strip()
                apply = (j.get("applyUrl") or "").strip()
                url = apply if urlsplit(apply).scheme == "https" else (
                    f"{ORIGIN}/jobs/{slug}" if slug and re.fullmatch(r"[A-Za-z0-9._~-]+", slug) else "")
                if not url:
                    continue
                locs: list[str] = []
                for loc in [j.get("location"), *(j.get("allLocations") or [])]:
                    if isinstance(loc, str) and loc.strip() and loc.strip().lower() not in [x.lower() for x in locs]:
                        locs.append(loc.strip())
                lo, hi = _num(j.get("salaryMin")), _num(j.get("salaryMax"))
                has_sal = lo is not None or hi is not None
                company = (j.get("company") or "").strip() or ((row.get("companies") or {}).get("name") or "").strip()
                jobs.append(self.job(
                    title=title, url=url, company=company or "Remotli",
                    location="; ".join(locs), locations=locs,
                    description=html_to_text(j.get("description") or ""),
                    posted_at=to_iso(j.get("publishedAt") or j.get("createdAt")),
                    salary_min=min(lo if lo is not None else hi, hi if hi is not None else lo) if has_sal else None,
                    salary_max=max(lo if lo is not None else hi, hi if hi is not None else lo) if has_sal else None,
                    currency=(j.get("salaryCurrency") or "").strip().upper() if has_sal else "",
                    source_id=str(j.get("id") or slug),
                ).validate())
                if len(jobs) >= ctx.max_jobs:
                    return jobs
            if len(rows) < PAGE:
                break
            page += 1
        return jobs


PROVIDER = Remotli()
