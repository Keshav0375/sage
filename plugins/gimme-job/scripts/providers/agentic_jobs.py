"""Agentic Engineering Jobs — public REST API (no auth, 30 req/60s).

GET https://agentic-engineering-jobs.com/api/v1/jobs?page=N  -> {data: [...], meta: {total, page, per_page}}
Mechanism from career-ops providers/agentic-jobs.mjs (MIT); code is our own.
"""
from __future__ import annotations

import re

from ._base import Context, Job, Provider, ProviderError, Target
from ._parse import html_to_text, to_iso

SITE = "https://agentic-engineering-jobs.com"
API = SITE + "/api/v1/jobs?page={page}"
MAX_PAGES = 40
SLUG_RE = re.compile(r"^[A-Za-z0-9_-]+$")


class AgenticJobs(Provider):
    name = "agentic-jobs"
    wave = "W3"
    kind = "board"
    tenant = False
    hosts = ("agentic-engineering-jobs.com",)

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        jobs: list[Job] = []
        seen: set[str] = set()
        for page in range(1, MAX_PAGES + 1):
            data = ctx.http.get_json(API.format(page=page))
            if not isinstance(data, dict) or not isinstance(data.get("data"), list):
                raise ProviderError("agentic-jobs: unexpected response shape")
            records = data["data"]
            meta = data.get("meta") or {}
            per_page = meta.get("per_page") if isinstance(meta.get("per_page"), int) and meta.get("per_page") > 0 else 50
            for r in records:
                title = (r.get("title") or "").strip()
                company = (r.get("companyName") or "").strip()
                slug = (r.get("slug") or "").strip()
                if not title or not company or not SLUG_RE.match(slug):
                    continue
                url = f"{SITE}/jobs/{slug}"
                if url in seen:
                    continue
                seen.add(url)
                countries = [c for c in (r.get("countries") or []) if isinstance(c, str)]
                loc = (r.get("location") or "").strip() or ", ".join(countries) or (r.get("geoRegion") or "")
                lo, hi = r.get("salaryMin"), r.get("salaryMax")
                jobs.append(self.job(
                    title=title, url=url, company=company, location=loc,
                    country=countries[0] if len(countries) == 1 else "",
                    posted_at=to_iso(r.get("postedAt")),
                    description=html_to_text(r.get("description") or ""),
                    salary_min=float(lo) if isinstance(lo, (int, float)) else None,
                    salary_max=float(hi) if isinstance(hi, (int, float)) else None,
                    currency=(r.get("salaryCurrency") or "").strip().upper(),
                    source_id=slug,
                ).validate())
                if len(jobs) >= ctx.max_jobs:
                    return jobs
            total = meta.get("total")
            if len(records) < per_page or (isinstance(total, int) and page * per_page >= total):
                break
        return jobs


PROVIDER = AgenticJobs()
