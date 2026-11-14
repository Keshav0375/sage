"""LaraJobs — RSS feed with job:company / job:location extension tags.

GET https://larajobs.com/feed
Mechanism from career-ops providers/larajobs.mjs (MIT); code is our own.
"""
from __future__ import annotations

import xml.etree.ElementTree as ET

from ._base import Context, Job, Provider, ProviderError, Target
from ._parse import feed_items, to_iso

FEED = "https://larajobs.com/feed"


class LaraJobs(Provider):
    name = "larajobs"
    wave = "W5"
    kind = "feed"
    tenant = False
    hosts = ("larajobs.com",)

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        try:
            items = feed_items(ctx.http.get_text(FEED))
        except ET.ParseError as e:
            raise ProviderError(f"larajobs: bad feed: {e}") from e
        kw = (target.query or "").lower().split()
        jobs: list[Job] = []
        for it in items:
            url = (it.get("link") or "").strip()
            title = (it.get("title") or "").strip()
            if not url.startswith("https://") or not title:
                continue
            if kw and not all(w in title.lower() for w in kw):
                continue
            jobs.append(self.job(
                title=title, url=url,
                company=(it.get("company") or it.get("author") or "").strip(),
                location=(it.get("location") or "").strip(),
                posted_at=to_iso(it.get("published")),
            ).validate())
            if len(jobs) >= ctx.max_jobs:
                break
        return jobs


PROVIDER = LaraJobs()
