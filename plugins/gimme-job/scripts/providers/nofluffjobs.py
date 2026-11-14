"""No Fluff Jobs (PL/CZ/SK/HU) — public search API, board-wide.

POST https://nofluffjobs.com/api/search/posting?pageTo=N&pageSize=20&...
Mechanism from career-ops providers/nofluffjobs.mjs (MIT); code is our own.
"""
from __future__ import annotations

from urllib.parse import urlencode

from ._base import Context, Job, Provider, ProviderError, Target
from ._parse import to_iso

API = "https://nofluffjobs.com/api/search/posting"
JOB_BASE = "https://nofluffjobs.com/pl/job/"
CRITERIA_KEYS = ["country", "withSalaryMatch", "city", "more", "employment", "requirement", "salary",
                 "jobPosition", "applicationStatus", "province", "company", "id", "category", "keyword",
                 "jobLanguage", "seniority"]


def _location(p: dict) -> tuple[str, list[str]]:
    parts: list[str] = []
    loc = p.get("location") or {}
    if p.get("fullyRemote") or loc.get("fullyRemote"):
        parts.append("Remote")
    for place in loc.get("places") or []:
        v = (place.get("city") or place.get("province") or (place.get("country") or {}).get("name") or "").strip()
        if v:
            parts.append(v)
    parts = list(dict.fromkeys(parts))
    return ", ".join(parts), parts


class NoFluffJobs(Provider):
    name = "nofluffjobs"
    wave = "W5"
    kind = "board"
    tenant = False
    hosts = ("nofluffjobs.com",)

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        o = target.options
        page_size = int(o.get("page_size") or 20)
        search = (o.get("search") or target.query or "").strip()
        qs = {"sort": "newest", "withSalaryMatch": "true", "pageSize": page_size,
              "salaryCurrency": str(o.get("currency") or "PLN").upper(),
              "salaryPeriod": o.get("salary_period") or "month",
              "region": o.get("region") or "pl", "language": o.get("language") or "pl-PL"}
        if search:
            body = {"criteria": "", "url": {"searchParam": search}, "rawSearch": search,
                    "pageSize": page_size, "withSalaryMatch": True}
        else:
            body = {"criteriaSearch": {k: [] for k in CRITERIA_KEYS}, "pageSize": page_size, "withSalaryMatch": True}
        jobs: dict[str, Job] = {}
        for page in range(1, int(o.get("max_pages") or 5) + 1):
            data = ctx.http.post_json(f"{API}?{urlencode({**qs, 'pageTo': page})}", body,
                                      headers={"Content-Type": "application/infiniteSearch+json"})
            if not isinstance(data, dict) or not isinstance(data.get("postings"), list):
                raise ProviderError("nofluffjobs: unexpected response, expected {postings: [...]}")
            for p in data["postings"]:
                slug = str(p.get("url") or p.get("id") or "").strip()
                if not slug or not p.get("title"):
                    continue
                url = JOB_BASE + slug
                if url in jobs:
                    continue
                loc, locs = _location(p)
                sal = p.get("salary") or {}
                jobs[url] = self.job(
                    title=p["title"], url=url, company=p.get("name", ""), location=loc, locations=locs,
                    workplace="remote" if (p.get("fullyRemote") or (p.get("location") or {}).get("fullyRemote")) else "",
                    posted_at=to_iso(p.get("posted")), source_id=str(p.get("id") or ""),
                    salary_min=sal.get("from"), salary_max=sal.get("to"), currency=sal.get("currency", "") if sal else "",
                ).validate()
                if len(jobs) >= ctx.max_jobs:
                    return list(jobs.values())
            total = int(data.get("totalPages") or 0)
            if not data["postings"] or (total and page >= total):
                break
        return list(jobs.values())


PROVIDER = NoFluffJobs()
