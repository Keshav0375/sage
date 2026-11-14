"""a16z speedrun talent network — public aggregator feed (no auth).

GET https://speedrun-talent-network.com/api/v1/jobs?page=N (0-indexed, 50/page)
-> {jobs: [{id, title, company, url, location, remote, published_at}], total_pages}
Mechanism from career-ops providers/a16z-speedrun-talent.mjs (MIT); code is our own.
"""
from __future__ import annotations

from urllib.parse import urlencode, urlsplit

from ._base import Context, Job, Provider, ProviderError, Target
from ._parse import to_iso

FEED = "https://speedrun-talent-network.com/api/v1/jobs"
HOST = "speedrun-talent-network.com"
PER_PAGE = 50


class SpeedrunTalent(Provider):
    name = "a16z-speedrun-talent"
    wave = "W3"
    kind = "board"
    tenant = False
    hosts = (HOST,)

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        max_pages = int(target.options.get("max_pages") or 6)
        jobs: list[Job] = []
        for page in range(max_pages):
            params = {"page": page}
            if target.query:
                params["q"] = target.query
            data = ctx.http.get_json(f"{FEED}?{urlencode(params)}")
            if not isinstance(data, dict) or not isinstance(data.get("jobs"), list):
                raise ProviderError("a16z-speedrun-talent: unexpected response shape")
            rows = data["jobs"]
            for j in rows:
                title = (j.get("title") or "").strip()
                url = (j.get("url") or "").strip()
                if not title or urlsplit(url).netloc != HOST:
                    continue
                base = (j.get("location") or "").strip()
                loc = ", ".join(x for x in (base, "Remote" if j.get("remote") is True else "") if x)
                jobs.append(self.job(
                    title=title, url=url, company=(j.get("company") or "").strip(),
                    location=loc, workplace="remote" if j.get("remote") is True else "",
                    posted_at=to_iso(j.get("published_at")),
                    source_id=str(j.get("id", "")),
                ).validate())
                if len(jobs) >= ctx.max_jobs:
                    return jobs
            tp = data.get("total_pages")
            if not rows:
                break
            if isinstance(tp, int) and tp > 0:
                if page + 1 >= tp:
                    break
            elif len(rows) < PER_PAGE:
                break
        return jobs


PROVIDER = SpeedrunTalent()
