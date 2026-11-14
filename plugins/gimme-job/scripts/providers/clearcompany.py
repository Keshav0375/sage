"""ClearCompany — https://careers-api.clearcompany.com/v1/<siteId>?pageIndex=&pageSize=.

Mechanism from career-ops providers/clearcompany.mjs (MIT); code is our own.
"""
from __future__ import annotations

import re
from urllib.parse import parse_qs, urlsplit

from ._base import Context, Job, Provider, ProviderError, Target
from ._parse import html_to_text, to_iso

API_HOST = "careers-api.clearcompany.com"
EMBED_HOST = "careers-content.clearcompany.com"
GUID = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.I)
PAGE_SIZE = 100
MAX_PAGES = 20


def _site_id(url: str) -> str:
    p = urlsplit((url or "").strip())
    if p.scheme != "https":
        return ""
    host = (p.hostname or "").lower()
    cand = ""
    if host == API_HOST:
        m = re.match(r"^/v1/([^/]+)/?$", p.path)
        cand = m.group(1) if m else ""
    elif host == EMBED_HOST:
        for k, v in parse_qs(p.query).items():
            if k.lower() == "siteid":
                cand = v[0]
                break
    return cand.lower() if GUID.match(cand) else ""


def _location(row: dict) -> str:
    if isinstance(row.get("location"), str) and row["location"].strip():
        return row["location"].strip()
    locs = row.get("locations")
    first = locs[0] if isinstance(locs, list) and locs else None
    if not isinstance(first, dict):
        return ""
    raw = (first.get("city"), first.get("subdivisionFullName") or first.get("subdivision"), first.get("country"))
    place = ", ".join(x.strip() for x in raw if isinstance(x, str) and x.strip())
    if first.get("isRemote") is True:
        return f"Remote ({place})" if place else "Remote"
    return place


class ClearCompany(Provider):
    name = "clearcompany"
    wave = "W4"
    kind = "ats"
    tenant = True
    hosts = ("clearcompany.com",)

    def detect(self, careers_url: str):
        s = _site_id(careers_url)
        return Target(slug=s, careers_url=careers_url, api_url=f"https://{API_HOST}/v1/{s}") if s else None

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        s = target.slug if GUID.match(target.slug or "") else (_site_id(target.api_url) or _site_id(target.careers_url))
        if not s:
            raise ProviderError("clearcompany needs a siteId (careers-api.clearcompany.com/v1/<siteId>)")
        jobs: list[Job] = []
        seen: set[str] = set()
        seen_raw = 0
        for page in range(MAX_PAGES):
            data = ctx.http.get_json(f"https://{API_HOST}/v1/{s}?pageIndex={page}&pageSize={PAGE_SIZE}")
            rows = data.get("results") if isinstance(data, dict) else None
            if not isinstance(rows, list):
                raise ProviderError("clearcompany: unexpected response, expected results[]")
            for r in rows:
                if not isinstance(r, dict):
                    continue
                title = re.sub(r"\s+", " ", r.get("positionTitle") or "").strip() if isinstance(r.get("positionTitle"), str) else ""
                url = (r.get("applyLink") or "").strip() if isinstance(r.get("applyLink"), str) else ""
                if not title or not url.startswith("https://") or url in seen:
                    continue
                seen.add(url)
                jobs.append(self.job(
                    title=title, url=url, company=target.company or s, location=_location(r),
                    workplace="remote" if isinstance(r.get("locations"), list) and r["locations"]
                    and isinstance(r["locations"][0], dict) and r["locations"][0].get("isRemote") is True else "",
                    posted_at=to_iso(r.get("postedDate") or r.get("openDate")),
                    description=html_to_text(r.get("description") or ""),
                    source_id=str(r.get("userDefinedId") or r.get("id") or ""),
                ).validate())
                if len(jobs) >= ctx.max_jobs:
                    return jobs
            seen_raw += len(rows)
            total = data.get("totalCount")
            if not rows or (isinstance(total, int) and seen_raw >= total):
                break
        return jobs


PROVIDER = ClearCompany()
