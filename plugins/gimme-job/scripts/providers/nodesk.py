"""NoDesk — public RSS feed of remote jobs (no auth).

GET https://nodesk.co/remote-jobs/index.xml ; title is "Role at Company"; no location tag.
Mechanism from career-ops providers/nodesk.mjs (MIT); code is our own.
"""
from __future__ import annotations

import xml.etree.ElementTree as ET
from urllib.parse import urlsplit

from ._base import Context, Job, Provider, ProviderError, Target
from ._parse import feed_items, to_iso

FEED = "https://nodesk.co/remote-jobs/index.xml"
HOST = "nodesk.co"


class NoDesk(Provider):
    name = "nodesk"
    wave = "W3"
    kind = "board"
    tenant = False
    hosts = (HOST,)

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        try:
            items = feed_items(ctx.http.get_text(FEED))
        except ET.ParseError as e:
            raise ProviderError(f"nodesk: bad feed: {e}") from e
        jobs: list[Job] = []
        for it in items:
            link = (it.get("link") or "").strip()
            p = urlsplit(link)
            host = p.netloc.lower()
            if p.scheme != "https" or not (host == HOST or host.endswith("." + HOST)):
                continue
            raw = (it.get("title") or "").strip()
            if not raw:
                continue
            idx = raw.lower().rfind(" at ")
            title, company = raw, target.company
            if idx > 0 and raw[:idx].strip() and raw[idx + 4:].strip():
                title, company = raw[:idx].strip(), raw[idx + 4:].strip()
            jobs.append(self.job(title=title, url=link, company=company,
                                 posted_at=to_iso(it.get("published"))).validate())
            if len(jobs) >= ctx.max_jobs:
                break
        return jobs


PROVIDER = NoDesk()
