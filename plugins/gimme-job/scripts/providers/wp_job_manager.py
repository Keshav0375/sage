"""Generic WP Job Manager boards — the plugin's RSS ``job_feed`` (no auth).

GET https://{host}/?feed=job_feed&posts_per_page=100[&paged=N]; host from Target.careers_url (or api_url).
Items carry title, link, pubDate, job_listing:company, job_listing:location, content:encoded.
Mechanism from career-ops providers/wp-job-manager.mjs (MIT); code is our own.
"""
from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from urllib.parse import urlsplit

from ._base import Context, Job, Provider, ProviderError, Target
from ._parse import feed_items, html_to_text, to_iso

PAGE_SIZE = 100


def _bare(host: str) -> str:
    return re.sub(r"^www\.", "", host.lower().rstrip("."))


class WpJobManager(Provider):
    name = "wp-job-manager"
    wave = "W3"
    kind = "ats"
    tenant = True
    hosts = ()

    def detect(self, careers_url: str):
        return None  # runs on arbitrary WordPress hosts; configured explicitly

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        p = urlsplit((target.careers_url or target.api_url or "").strip())
        host = (p.hostname or "").lower().rstrip(".")
        if p.scheme != "https" or "." not in host or p.username or p.port:
            raise ProviderError("wp-job-manager needs an https careers_url (the board's address)")
        max_pages = min(int(target.options.get("max_pages") or 20), 100)
        jobs: list[Job] = []
        seen: set[str] = set()
        for page in range(1, max_pages + 1):
            url = f"https://{host}/?feed=job_feed&posts_per_page={PAGE_SIZE}" + (f"&paged={page}" if page > 1 else "")
            xml = ctx.http.get_text(url)
            if not re.search(r"<rss\b", xml, re.I) or not re.search(r"<channel\b", xml, re.I):
                raise ProviderError(f"wp-job-manager: expected an RSS job_feed from {host}")
            try:
                items = feed_items(xml)
            except ET.ParseError as e:
                raise ProviderError(f"wp-job-manager: bad feed: {e}") from e
            before = len(jobs)
            for it in items:
                link = (it.get("link") or "").strip()
                lp = urlsplit(link)
                if lp.scheme != "https" or _bare(lp.hostname or "") != _bare(host) or link in seen:
                    continue
                title = (it.get("title") or "").strip()
                if not title:
                    continue
                seen.add(link)
                jobs.append(self.job(
                    title=title, url=link, company=(it.get("company") or "").strip() or target.company,
                    location=(it.get("location") or "").strip(),
                    posted_at=to_iso(it.get("published")),
                    description=html_to_text(it.get("description") or ""),
                ).validate())
                if len(jobs) >= ctx.max_jobs:
                    return jobs
            if items and not jobs:
                raise ProviderError(f"wp-job-manager: {len(items)} items from {host} but none usable")
            if len(items) < PAGE_SIZE or (page > 1 and len(jobs) == before):
                break
        return jobs


PROVIDER = WpJobManager()
