"""Arbeitnow — public job-board API (no auth). Board-wide.

GET https://www.arbeitnow.com/api/job-board-api?page=N  ->  {"data": [...]}
Mechanism from career-ops providers/arbeitnow.mjs (MIT); code is our own.
"""
from __future__ import annotations

from ._base import Context, Job, Provider, ProviderError, Target
from ._parse import html_to_text, to_iso

API = "https://www.arbeitnow.com/api/job-board-api"
PER_PAGE = 100


class Arbeitnow(Provider):
    name = "arbeitnow"
    wave = "W5"
    kind = "board"
    tenant = False
    hosts = ("www.arbeitnow.com",)

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        pages = int(target.options.get("max_pages") or 3)
        kw = (target.query or "").lower().split()
        jobs: list[Job] = []
        for page in range(1, min(pages, 50) + 1):
            data = ctx.http.get_json(f"{API}?page={page}")
            rows = (data or {}).get("data")
            if not isinstance(rows, list):
                raise ProviderError("arbeitnow: unexpected response, expected {data: [...]}")
            for j in rows:
                title = (j.get("title") or "").strip()
                url = (j.get("url") or "").strip()
                if not title or not url:
                    continue
                if kw and not all(w in f"{title} {' '.join(j.get('tags') or [])}".lower() for w in kw):
                    continue
                loc = (j.get("location") or "").strip()
                jt = j.get("job_types") or []
                jobs.append(self.job(
                    title=title, url=url,
                    company=(j.get("company_name") or "").strip(),
                    location=loc,
                    workplace="remote" if j.get("remote") is True else "",
                    posted_at=to_iso(j.get("created_at")),
                    description=html_to_text(j.get("description") or ""),
                    source_id=str(j.get("slug") or ""),
                    extra={"tags": j.get("tags") or [], "job_types": jt},
                ).validate())
                if len(jobs) >= ctx.max_jobs:
                    return jobs
            if len(rows) < PER_PAGE:
                break
        return jobs


PROVIDER = Arbeitnow()
