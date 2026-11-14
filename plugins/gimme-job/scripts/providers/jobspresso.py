"""Jobspresso — public WordPress job_feed RSS (no auth).

GET https://jobspresso.co/feed/job_feed/?posts_per_page=100
Items carry title, link, pubDate, job_listing:company, job_listing:location, content:encoded.
Mechanism from career-ops providers/jobspresso.mjs (MIT); code is our own.
"""
from __future__ import annotations

import xml.etree.ElementTree as ET
from urllib.parse import urlsplit

from ._base import Context, Job, Provider, ProviderError, Target
from ._parse import feed_items, html_to_text, to_iso

BASE = "https://jobspresso.co/feed/job_feed/"
HOST = "jobspresso.co"


class Jobspresso(Provider):
    name = "jobspresso"
    wave = "W3"
    kind = "board"
    tenant = False
    hosts = (HOST,)

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        n = target.options.get("posts_per_page")
        count = min(n, 100) if isinstance(n, int) and n > 0 else 100
        try:
            items = feed_items(ctx.http.get_text(f"{BASE}?posts_per_page={count}"))
        except ET.ParseError as e:
            raise ProviderError(f"jobspresso: bad feed: {e}") from e
        jobs: list[Job] = []
        for it in items:
            link = (it.get("link") or "").strip()
            p = urlsplit(link)
            h = p.netloc.lower()
            if p.scheme != "https" or not (h == HOST or h.endswith("." + HOST)):
                continue
            title = (it.get("title") or "").strip()
            if not title:
                continue
            jobs.append(self.job(
                title=title, url=link, company=(it.get("company") or "").strip(),
                location=(it.get("location") or "").strip(),
                posted_at=to_iso(it.get("published")),
                description=html_to_text(it.get("description") or ""),
            ).validate())
            if len(jobs) >= ctx.max_jobs:
                break
        return jobs


PROVIDER = Jobspresso()
