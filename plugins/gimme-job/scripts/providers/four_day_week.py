"""4 Day Week — public JSON API (no auth).

GET https://4dayweek.io/api/jobs?page=N -> {jobs: [{id,title,slug,company_name,locations,work_arrangement,posted(epoch s),is_expired}], has_more}
The feed has no URL field: canonical page is https://4dayweek.io/job/<slug>.
Mechanism from career-ops providers/4dayweek.mjs (MIT); code is our own.
"""
from __future__ import annotations

import re
from urllib.parse import quote

from ._base import Context, Job, Provider, ProviderError, Target
from ._parse import to_iso

FEED = "https://4dayweek.io/api/jobs"
JOB_BASE = "https://4dayweek.io/job"
PER_PAGE = 25
SLUG_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9-]*$")


class FourDayWeek(Provider):
    name = "4dayweek"
    wave = "W3"
    kind = "board"
    tenant = False
    hosts = ("4dayweek.io",)

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        max_pages = min(int(target.options.get("max_pages") or 3), 50)
        jobs: list[Job] = []
        for page in range(1, max_pages + 1):
            data = ctx.http.get_json(f"{FEED}?page={page}")
            if not isinstance(data, dict) or not isinstance(data.get("jobs"), list):
                raise ProviderError("4dayweek: unexpected response shape")
            for j in data["jobs"]:
                if j.get("is_expired") is True:
                    continue
                title = (j.get("title") or "").strip()
                slug = (j.get("slug") or "").strip()
                if not title or not SLUG_RE.match(slug):
                    continue
                locs = [x for x in (j.get("locations") or []) if isinstance(x, dict)]
                first = locs[0] if locs else {}
                base = ", ".join(x for x in (first.get("city"), first.get("country")) if x)
                remote = j.get("work_arrangement") == "remote" or first.get("work_arrangement") == "remote"
                company = j.get("company_name") or (j.get("company") or {}).get("name") or ""
                posted = j.get("posted")
                jobs.append(self.job(
                    title=title, url=f"{JOB_BASE}/{quote(slug)}", company=company.strip(),
                    location=", ".join(x for x in (base, "Remote" if remote else "") if x),
                    country=(first.get("country") or ""),
                    workplace="remote" if remote else "",
                    posted_at=to_iso(posted) if isinstance(posted, (int, float)) else "",
                    source_id=str(j.get("id", "")),
                ).validate())
                if len(jobs) >= ctx.max_jobs:
                    return jobs
            if data.get("has_more") is False or len(data["jobs"]) < PER_PAGE:
                break
        return jobs


PROVIDER = FourDayWeek()
