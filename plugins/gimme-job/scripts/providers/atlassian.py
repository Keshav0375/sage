"""Atlassian Careers — public listings endpoint (JSON array, no auth).

GET https://www.atlassian.com/endpoint/careers/listings -> [{id, title, locations[], applyUrl, portalJobPost:{portalUrl}}]
Mechanism from career-ops providers/atlassian.mjs (MIT); code is our own.
"""
from __future__ import annotations

import re
from urllib.parse import urlsplit

from ._base import Context, Job, Provider, ProviderError, Target

LISTINGS = "https://www.atlassian.com/endpoint/careers/listings"
HOST = "www.atlassian.com"


class Atlassian(Provider):
    name = "atlassian"
    wave = "W3"
    kind = "company"
    tenant = False
    hosts = (HOST,)

    def detect(self, careers_url: str):
        p = urlsplit(careers_url or "")
        if p.netloc.lower() == HOST and re.search(r"careers", p.path, re.I):
            return Target(company="Atlassian", careers_url=careers_url, api_url=LISTINGS)
        return None

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        data = ctx.http.get_json(LISTINGS)
        if not isinstance(data, list):
            raise ProviderError("atlassian: listings did not return an array")
        jobs: list[Job] = []
        for j in data:
            if not isinstance(j, dict):
                continue
            title = (j.get("title") or "").strip() if isinstance(j.get("title"), str) else ""
            url = ""
            for raw in ((j.get("portalJobPost") or {}).get("portalUrl"), j.get("applyUrl")):
                if isinstance(raw, str) and raw.strip().startswith(("http://", "https://")):
                    url = raw.strip()
                    break
            if not title or not url:
                continue
            locs = [" ".join(str(l).split()) for l in (j.get("locations") or []) if str(l).strip()]
            jobs.append(self.job(
                title=title, url=url, company="Atlassian", location="; ".join(locs), locations=locs,
                department=(j.get("category") or "") if isinstance(j.get("category"), str) else "",
                source_id=str(j.get("id") or ""),
            ).validate())
            if len(jobs) >= ctx.max_jobs:
                break
        return jobs


PROVIDER = Atlassian()
