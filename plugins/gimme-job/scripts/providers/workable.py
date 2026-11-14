"""Workable — public widget API (no auth).

GET https://apply.workable.com/api/v1/widget/accounts/{slug}?details=true
Mechanism from career-ops providers/workable.mjs (MIT); code is our own.
Simplified: no jobs.md fallback feed.
"""
from __future__ import annotations

import re
from urllib.parse import urlsplit

from ._base import Context, Job, Provider, ProviderError, Target
from ._parse import html_to_text, to_iso

API = "https://apply.workable.com/api/v1/widget/accounts/{slug}?details=true"


def _loc(r: dict) -> str:
    city, country = (r.get("city") or "").strip(), (r.get("country") or "").strip()
    state = (r.get("state") or "").strip()
    if city:
        return ", ".join(x for x in (city, country) if x)
    return ", ".join(x for x in (state or "", country) if x) if (state or country) else ""


class Workable(Provider):
    name = "workable"
    wave = "W1"
    kind = "ats"
    tenant = True
    hosts = ("workable.com",)

    def detect(self, careers_url: str):
        p = urlsplit(careers_url or "")
        if p.netloc.lower() != "apply.workable.com":
            return None
        parts = [x for x in p.path.split("/") if x]
        if not parts or parts[0] in ("j", "api") or not re.match(r"^[A-Za-z0-9][A-Za-z0-9_-]*$", parts[0]):
            return None
        return Target(slug=parts[0], careers_url=careers_url, api_url=API.format(slug=parts[0]))

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        slug = target.slug or (self.detect(target.careers_url) or Target()).slug
        if not slug:
            raise ProviderError("workable needs an account slug")
        data = ctx.http.get_json(target.api_url or API.format(slug=slug),
                                 headers={"Referer": f"https://apply.workable.com/{slug}/"})
        if not isinstance(data, dict) or not isinstance(data.get("jobs"), list):
            raise ProviderError("workable: expected {jobs: [...]}")
        by_url: dict[str, Job] = {}
        for r in data["jobs"]:
            title = (r.get("title") or "").strip()
            url = r.get("shortlink") or r.get("url") or ""
            if not title or urlsplit(url).netloc != "apply.workable.com":
                continue
            loc = _loc(r)
            if url in by_url:                       # fanned-out sibling of the same posting
                j = by_url[url]
                if loc and loc not in j.locations:
                    j.locations.append(loc)
                continue
            by_url[url] = self.job(
                title=title, url=url, company=target.company or data.get("name") or slug,
                locations=[loc] if loc else [],
                workplace="remote" if r.get("telecommuting") else "",
                department=r.get("department") or "",
                posted_at=to_iso(r.get("published_on") or r.get("created_at")),
                description=html_to_text(r.get("description", "")),
                source_id=str(r.get("shortcode", "")),
            )
            if len(by_url) >= ctx.max_jobs:
                break
        return [j.validate() for j in by_url.values()]


PROVIDER = Workable()
