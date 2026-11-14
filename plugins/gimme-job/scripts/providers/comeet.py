"""Comeet — public careers-api positions endpoint (needs the full api url incl. token).

https://www.comeet.co/careers-api/2.0/company/<uid>/positions?token=<token>&details=false
Mechanism from career-ops providers/comeet.mjs (MIT).
"""
from __future__ import annotations

import re
from urllib.parse import urlsplit

from ._base import Context, Job, Provider, ProviderError, Target
from ._parse import to_iso


def _is_api(url: str) -> bool:
    p = urlsplit(url or "")
    return p.scheme == "https" and p.netloc.lower() == "www.comeet.co" and p.path.startswith("/careers-api/")


def _redact(url: str) -> str:
    return re.sub(r"([?&]token=)[^&#]*", r"\1REDACTED", url or "")


class Comeet(Provider):
    name = "comeet"
    wave = "W2"
    kind = "ats"
    tenant = True
    hosts = ("www.comeet.co",)

    def detect(self, careers_url: str):
        if not _is_api(careers_url):
            return None
        m = re.search(r"/company/([^/]+)/", careers_url)
        return Target(slug=m.group(1) if m else "", careers_url=careers_url, api_url=careers_url)

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        api = next((u for u in (target.api_url, target.careers_url) if _is_api(u)), "")
        if not api:
            raise ProviderError("comeet needs the full careers-api positions url (with token) as api_url")
        data = ctx.http.get_json(api)
        if not isinstance(data, list):
            raise ProviderError("comeet: expected an array of positions")
        company = target.company or target.slug
        jobs: list[Job] = []
        for j in data:
            if not isinstance(j, dict):
                continue
            url = next((u for u in (j.get("url_active_page"), j.get("url_comeet_hosted_page"))
                        if isinstance(u, str) and u.startswith("https://")), "")
            loc = j.get("location") if isinstance(j.get("location"), dict) else {}
            base = str(loc.get("name") or "").strip()
            if loc.get("is_remote") and "remote" not in base.lower():
                base = ", ".join(x for x in (base, "Remote") if x)
            title = str(j.get("name") or "").strip()
            if not title or not url:
                continue
            jobs.append(self.job(title=title, url=url, company=company, location=base,
                                 workplace="remote" if loc.get("is_remote") else "",
                                 department=str(j.get("department") or ""), posted_at=to_iso(j.get("time_updated")),
                                 source_id=str(j.get("uid") or "")).validate())
            if len(jobs) >= ctx.max_jobs:
                break
        return jobs


PROVIDER = Comeet()
