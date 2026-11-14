"""JobStreet / SEEK-family — public jobsearch v5 JSON API.

GET https://<host>/api/jobsearch/v5/search?siteKey=ID-Main&keywords=..&where=..&pageSize=30&page=N
Mechanism from career-ops providers/jobstreet.mjs (MIT); code is our own.
Target options: host (default id.jobstreet.com), siteKey (default ID-Main), page_size, max_pages.
"""
from __future__ import annotations

from urllib.parse import urlencode

from ._base import Context, Job, Provider, ProviderError, Target
from ._parse import to_iso

ALLOWED = {"id.jobstreet.com", "www.jobstreet.com", "www.jobstreet.co.id", "jobstreet.com", "jobstreet.co.id",
           "sg.jobstreet.com", "my.jobstreet.com", "hk.jobsdb.com"}
ID_HOSTS = {"id.jobstreet.com", "www.jobstreet.co.id", "jobstreet.co.id"}


class JobStreet(Provider):
    name = "jobstreet"
    wave = "W5"
    kind = "board"
    tenant = False
    hosts = tuple(sorted(ALLOWED))

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        o = target.options
        host = o.get("host") or "id.jobstreet.com"
        if host not in ALLOWED:
            raise ProviderError(f"jobstreet: host not allowed: {host}")
        size = min(int(o.get("page_size") or 30), 100)
        pages = min(int(o.get("max_pages") or 3), 500)
        base = f"https://{host}"
        detail = "/id/job/" if host in ID_HOSTS else "/job/"
        jobs: list[Job] = []
        for page in range(1, pages + 1):
            params = {"siteKey": o.get("siteKey") or "ID-Main", "pageSize": size, "page": page}
            if target.query:
                params["keywords"] = target.query
            if target.location:
                params["where"] = target.location
            data = ctx.http.get_json(f"{base}/api/jobsearch/v5/search?{urlencode(params)}")
            rows = (data or {}).get("data") or []
            if not rows:
                break
            for it in rows:
                jid = str(it.get("id") or "").strip()
                title = str(it.get("title") or "").strip()
                if not jid or not title:
                    continue
                locs = [str(l.get("label") or "").strip() for l in it.get("locations") or [] if l.get("label")]
                jobs.append(self.job(
                    title=title, url=f"{base}{detail}{jid}",
                    company=str((it.get("advertiser") or {}).get("description") or it.get("companyName") or "").strip(),
                    location=locs[0] if locs else "", locations=locs,
                    posted_at=to_iso(it.get("listingDate")), source_id=jid,
                    extra={"work_types": it.get("workTypes") or []},
                ).validate())
                if len(jobs) >= ctx.max_jobs:
                    return jobs
            if len(rows) < size:
                break
        return jobs


PROVIDER = JobStreet()
