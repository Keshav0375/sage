"""Landing.jobs (PT/EU) — public v1 jobs array.

GET https://landing.jobs/api/v1/jobs  ->  [ {...}, ... ]
Mechanism from career-ops providers/landingjobs.mjs (MIT); code is our own.
Company is derived from the /at/<company>/ URL segment (the feed has no company field).
"""
from __future__ import annotations

import re
from urllib.parse import urlsplit

from ._base import Context, Job, Provider, ProviderError, Target
from ._parse import to_iso

FEED = "https://landing.jobs/api/v1/jobs"


def company_from_url(url: str) -> str:
    segs = [s for s in urlsplit(url).path.split("/") if s]
    if len(segs) < 2 or segs[0] != "at":
        return ""
    return re.sub(r"\b\w", lambda m: m.group(0).upper(), re.sub(r"[-_]+", " ", segs[1]).strip())


class LandingJobs(Provider):
    name = "landingjobs"
    wave = "W5"
    kind = "board"
    tenant = False
    hosts = ("landing.jobs",)

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        data = ctx.http.get_json(FEED)
        if not isinstance(data, list):
            raise ProviderError("landingjobs: unexpected response, expected a JSON array")
        kw = (target.query or "").lower().split()
        jobs: list[Job] = []
        for j in data:
            title = str(j.get("title") or "").strip()
            url = str(j.get("url") or "").strip()
            p = urlsplit(url)
            if not title or p.scheme != "https" or p.netloc != "landing.jobs":
                continue
            if kw and not all(w in title.lower() for w in kw):
                continue
            first = (j.get("locations") or [{}])[0] or {}
            city, cc = str(first.get("city") or "").strip(), str(first.get("country_code") or "").strip()
            remote = j.get("remote") is True
            jobs.append(self.job(
                title=title, url=url, company=company_from_url(url),
                location=", ".join(x for x in (", ".join(y for y in (city, cc) if y), "Remote" if remote else "") if x),
                country=cc, workplace="remote" if remote else "",
                posted_at=to_iso(j.get("published_at") or j.get("created_at")),
                source_id=str(j.get("id") or ""),
            ).validate())
            if len(jobs) >= ctx.max_jobs:
                break
        return jobs


PROVIDER = LandingJobs()
