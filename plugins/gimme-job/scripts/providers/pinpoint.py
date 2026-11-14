"""Pinpoint — public postings feed at https://<slug>.pinpointhq.com/postings.json.

Mechanism from career-ops providers/pinpoint.mjs (MIT).
"""
from __future__ import annotations

import re
from urllib.parse import urlsplit

from ._base import Context, Job, Provider, ProviderError, Target
from ._parse import employment_from, html_to_text, workplace_from

HOST_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.pinpointhq\.com$")
DEMO_MARKER = "youtube.com/embed/https://www.youtube.com/embed/pFxm6fszrpw"


def _origin(url: str) -> str:
    p = urlsplit(url or "")
    host = p.netloc.lower()
    return f"https://{host}" if p.scheme == "https" and HOST_RE.match(host) else ""


class Pinpoint(Provider):
    name = "pinpoint"
    wave = "W2"
    kind = "ats"
    tenant = True
    hosts = ("pinpointhq.com",)

    def detect(self, careers_url: str):
        o = _origin(careers_url)
        if not o:
            return None
        return Target(slug=urlsplit(o).netloc.split(".")[0], careers_url=careers_url, api_url=f"{o}/postings.json")

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        o = _origin(target.api_url) or _origin(target.careers_url)
        if not o:
            raise ProviderError("pinpoint needs an https <slug>.pinpointhq.com url")
        data = ctx.http.get_json(f"{o}/postings.json")
        rows = data.get("data") if isinstance(data, dict) else None
        if not isinstance(rows, list):
            raise ProviderError("pinpoint: expected data[]")
        company = target.company or urlsplit(o).netloc.split(".")[0]
        jobs: list[Job] = []
        for j in rows:
            if not isinstance(j, dict) or DEMO_MARKER in str(j.get("description") or ""):
                continue
            title = str(j.get("title") or "").strip()
            url = str(j.get("url") or "").strip()
            if not title or not url.startswith("https://"):
                continue
            loc = j.get("location") if isinstance(j.get("location"), dict) else {}
            place = str(loc.get("name") or "").strip() or ", ".join(x for x in (loc.get("city"), loc.get("province")) if x)
            dept = j.get("department")
            jobs.append(self.job(title=title, url=url, company=company, location=place,
                                 workplace=workplace_from(j.get("workplace_type")),
                                 employment=employment_from(j.get("employment_type")),
                                 department=(dept.get("name") if isinstance(dept, dict) else "") or "",
                                 description=html_to_text(str(j.get("description") or "")),
                                 source_id=str(j.get("id") or "")).validate())
            if len(jobs) >= ctx.max_jobs:
                break
        return jobs


PROVIDER = Pinpoint()
