"""Rippling ATS — public board API: ats.rippling.com/api/v2/board/<slug>/jobs.

Mechanism from career-ops providers/rippling.mjs (MIT).
"""
from __future__ import annotations

import re
from urllib.parse import quote, urlsplit

from ._base import Context, Job, Provider, ProviderError, Target

HOST = "ats.rippling.com"
SLUG_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?$")
PAGE_SIZE = 1000
MAX_PAGES = 10


def _slug(url: str) -> str:
    p = urlsplit(url or "")
    if p.scheme != "https" or p.netloc.lower() != HOST:
        return ""
    segs = [s for s in p.path.split("/") if s]
    return segs[0] if segs and SLUG_RE.match(segs[0]) else ""


class Rippling(Provider):
    name = "rippling"
    wave = "W2"
    kind = "ats"
    tenant = True
    hosts = (HOST,)

    def detect(self, careers_url: str):
        s = _slug(careers_url)
        if not s:
            return None
        return Target(slug=s, careers_url=careers_url, api_url=f"https://{HOST}/api/v2/board/{quote(s)}/jobs")

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        slug = target.slug or _slug(target.careers_url)
        if not slug:
            raise ProviderError("rippling needs an ats.rippling.com/<slug> url")
        jobs: list[Job] = []
        for page in range(MAX_PAGES):
            data = ctx.http.get_json(f"https://{HOST}/api/v2/board/{quote(slug)}/jobs?page={page}&pageSize={PAGE_SIZE}")
            if not isinstance(data, dict) or not isinstance(data.get("items"), list):
                raise ProviderError("rippling: unexpected response, no items[]")
            for j in data["items"]:
                u = urlsplit(j.get("url") or "")
                title = (j.get("name") or "").strip()
                if not title or u.scheme != "https" or u.netloc.lower() != HOST:
                    continue
                locs = [str(l.get("name")).strip() for l in j.get("locations") or [] if isinstance(l, dict) and l.get("name")]
                dept = j.get("department")
                jobs.append(self.job(title=title, url=j["url"], company=target.company or slug, locations=locs,
                                     location=" · ".join(locs),
                                     department=(dept.get("name") if isinstance(dept, dict) else dept) or "",
                                     source_id=str(j.get("id") or "")).validate())
                if len(jobs) >= ctx.max_jobs:
                    return jobs
            if len(data["items"]) < PAGE_SIZE:
                break
        return jobs


PROVIDER = Rippling()
