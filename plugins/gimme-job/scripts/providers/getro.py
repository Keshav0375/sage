"""Getro — public talent-network search API (no auth), used by many VC portfolio job boards.

POST https://api.getro.com/api/v2/collections/{collection_id}/search/jobs
The collection id is read from the portal page's __NEXT_DATA__ (props.pageProps.network.id) unless
given in ``Target.options["collection"]``.
Mechanism from career-ops providers/getro.mjs (MIT); code is our own.
"""
from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from urllib.parse import urlsplit

from ._base import Context, Job, Provider, ProviderError, Target
from ._parse import dig, next_data, to_iso

API = "https://api.getro.com/api/v2/collections/{cid}/search/jobs"
PER_PAGE = 20


class Getro(Provider):
    name = "getro"
    wave = "W1"
    kind = "ats"
    tenant = True
    hosts = ("getro.com",)

    def detect(self, careers_url: str):
        p = urlsplit(careers_url or "")
        host = p.netloc.lower()
        m = re.match(r"^/api/v2/collections/(\d+)", p.path)
        if host == "api.getro.com" and m:
            return Target(slug=m.group(1), careers_url=careers_url, api_url=API.format(cid=m.group(1)),
                          options={"collection": m.group(1)})
        if host.endswith(".getro.com") and host not in ("api.getro.com", "www.getro.com"):
            return Target(slug=host.split(".")[0], careers_url=careers_url)
        return None

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        cid = str(target.options.get("collection") or "").strip()
        if not cid and target.api_url:
            m = re.search(r"/collections/(\d+)/", target.api_url)
            cid = m.group(1) if m else ""
        careers = target.careers_url
        if not cid:
            if not careers.startswith("https://"):
                raise ProviderError("getro needs an https careers_url or options['collection']")
            data = next_data(ctx.http.get_text(careers))
            raw = dig(data, "props.pageProps.network.id")
            cid = str(raw) if raw is not None and re.fullmatch(r"\d+", str(raw)) else ""
            if not cid:
                raise ProviderError("getro: could not resolve collection id from the portal page")
        origin = "{0.scheme}://{0.netloc}".format(urlsplit(careers)) if careers else "https://getro.com"
        max_pages = int(target.options.get("max_pages", 40))
        max_age = int(target.options.get("max_age_days", 90))
        cutoff = datetime.now(timezone.utc) - timedelta(days=max_age) if max_age > 0 else None
        jobs: list[Job] = []
        total = None
        for page in range(max_pages):
            if total is not None and page * PER_PAGE >= total:
                break
            data = ctx.http.post_json(API.format(cid=cid), {"hitsPerPage": PER_PAGE, "page": page, "filters": {"page": page}, "query": ""},
                                      headers={"Referer": origin + "/"})
            res = (data or {}).get("results") or {}
            rows = res.get("jobs") if isinstance(res.get("jobs"), list) else []
            if isinstance(res.get("count"), int):
                total = res["count"]
            if not rows:
                break
            old = False
            for j in rows:
                url = j.get("url") or ""
                if not url:
                    continue
                posted = to_iso(j.get("created_at"))
                if cutoff and posted:
                    try:
                        dt = datetime.fromisoformat(posted)
                        if dt.tzinfo is None:
                            dt = dt.replace(tzinfo=timezone.utc)
                        if dt < cutoff:
                            old = old or j.get("featured") is not True
                            continue
                    except ValueError:
                        pass
                places = [l.strip() for l in (j.get("locations") or j.get("searchable_locations") or []) if isinstance(l, str) and l.strip()]
                remote = j.get("work_mode") == "remote"
                if remote and not any(re.search("remote", l, re.I) for l in places):
                    places.append("Remote")
                extra = {}
                lo, hi = j.get("compensation_amount_min_cents"), j.get("compensation_amount_max_cents")
                if (lo or hi) and (j.get("compensation_period") or "year") == "year":
                    lo_, hi_ = (lo or hi) / 100, (hi or lo) / 100
                    extra = dict(salary_min=lo_, salary_max=hi_, currency=j.get("compensation_currency") or "", salary_period="year")
                org = j.get("organization") or {}
                jobs.append(self.job(
                    title=j.get("title", ""), url=url,
                    company=org.get("name") or j.get("organization_name") or target.company,
                    location=", ".join(places), locations=places, workplace="remote" if remote else "",
                    posted_at=posted, source_id=str(j.get("id", "")), **extra,
                ).validate())
                if len(jobs) >= ctx.max_jobs:
                    return jobs
            if old:
                break
        return jobs


PROVIDER = Getro()
