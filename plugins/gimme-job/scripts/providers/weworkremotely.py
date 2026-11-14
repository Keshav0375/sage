"""We Work Remotely — public RSS feed (no auth).

GET https://weworkremotely.com/remote-jobs.rss
Mechanism from career-ops providers/weworkremotely.mjs (MIT); code is our own.
"""
from __future__ import annotations

import xml.etree.ElementTree as ET
from urllib.parse import urlsplit

from ._base import Context, Job, Provider, ProviderError, Target
from ._parse import html_to_text, to_iso

FEED = "https://weworkremotely.com/remote-jobs.rss"


class WeWorkRemotely(Provider):
    name = "weworkremotely"
    wave = "W1"
    kind = "feed"
    tenant = False
    hosts = ("weworkremotely.com",)

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        try:
            root = ET.fromstring(ctx.http.get_text(FEED).lstrip("﻿").strip())
        except ET.ParseError as e:
            raise ProviderError(f"weworkremotely: bad feed: {e}") from e
        words = [w.lower() for w in (target.query or "").split()]
        jobs: list[Job] = []
        for item in root.iter("item"):
            f = {c.tag.rsplit("}", 1)[-1]: (c.text or "").strip() for c in item}
            url, raw = f.get("link", ""), f.get("title", "")
            host = urlsplit(url).netloc.lower()
            if not raw or not url.startswith("https://") or not (host == "weworkremotely.com" or host.endswith(".weworkremotely.com")):
                continue
            company, title = "", raw
            if ":" in raw:
                c, t = raw.split(":", 1)
                if c.strip() and t.strip():
                    company, title = c.strip(), t.strip()
            if words and not any(w in (title + " " + company).lower() for w in words):
                continue
            jobs.append(self.job(
                title=title, url=url, company=company, location=f.get("region") or f.get("category", ""),
                workplace="remote", posted_at=to_iso(f.get("pubDate")),
                description=html_to_text(f.get("description", "")), department=f.get("category", ""),
                source_id=f.get("guid", ""),
            ).validate())
            if len(jobs) >= ctx.max_jobs:
                break
        return jobs


PROVIDER = WeWorkRemotely()
