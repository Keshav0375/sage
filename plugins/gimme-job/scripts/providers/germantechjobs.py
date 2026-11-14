"""GermanTechJobs — board-wide RSS feed.

GET https://germantechjobs.de/rss  (item title: "Role @ Company [salary €]")
Mechanism from career-ops providers/germantechjobs.mjs (MIT); code is our own.
"""
from __future__ import annotations

import re
import xml.etree.ElementTree as ET

from ._base import Context, Job, Provider, ProviderError, Target
from ._parse import feed_items, html_to_text, to_iso

FEED = "https://germantechjobs.de/rss"


class GermanTechJobs(Provider):
    name = "germantechjobs"
    wave = "W5"
    kind = "feed"
    tenant = False
    hosts = ("germantechjobs.de",)

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        text = ctx.http.get_text(target.api_url or FEED)
        try:
            items = feed_items(text)
        except ET.ParseError as e:
            raise ProviderError(f"germantechjobs: bad feed: {e}") from e
        kw = (target.query or "").lower().split()
        jobs: list[Job] = []
        for it in items:
            url = (it.get("link") or it.get("id") or "").strip()
            raw = (it.get("title") or "").strip()
            if not url.startswith("https://") or not raw:
                continue
            raw = re.sub(r"\s*\[[^\]]*€[^\]]*\]\s*$", "", raw).strip()
            title, sep, company = raw.rpartition(" @ ")
            if not sep or not title.strip() or not company.strip():
                continue
            if kw and not all(w in f"{title} {company}".lower() for w in kw):
                continue
            jobs.append(self.job(
                title=title.strip(), url=url.split("?")[0], company=company.strip(), country="DE",
                posted_at=to_iso(it.get("published")),
                description=html_to_text(it.get("description") or ""),
            ).validate())
            if len(jobs) >= ctx.max_jobs:
                break
        return jobs


PROVIDER = GermanTechJobs()
