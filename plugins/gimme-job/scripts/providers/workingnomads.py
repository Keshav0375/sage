"""Working Nomads — public JSON feed (array of postings, no auth).

GET https://www.workingnomads.com/api/exposed_jobs/
Mechanism from career-ops providers/workingnomads.mjs (MIT); code is our own.
"""
from __future__ import annotations

from ._base import Context, Job, Provider, ProviderError, Target
from ._parse import html_to_text, to_iso

FEED = "https://www.workingnomads.com/api/exposed_jobs/"


class WorkingNomads(Provider):
    name = "workingnomads"
    wave = "W3"
    kind = "board"
    tenant = False
    hosts = ("workingnomads.com",)

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        data = ctx.http.get_json(FEED)
        if not isinstance(data, list):
            raise ProviderError("workingnomads: expected a JSON array")
        jobs: list[Job] = []
        for j in data:
            if not isinstance(j, dict):
                continue
            title = (j.get("title") or "").strip()
            url = (j.get("url") or "").strip()
            if not title or not url.lower().startswith(("http://", "https://")):
                continue
            jobs.append(self.job(
                title=title, url=url,
                company=(j.get("company_name") or "").strip(),
                location=(j.get("location") or "").strip(),
                posted_at=to_iso(j.get("pub_date")),
                description=html_to_text(j.get("description") or ""),
                department=(j.get("category_name") or "").strip(),
            ).validate())
            if len(jobs) >= ctx.max_jobs:
                break
        return jobs


PROVIDER = WorkingNomads()
