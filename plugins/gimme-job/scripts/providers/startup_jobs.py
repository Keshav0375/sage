"""Startup Jobs — public RSS feed (no auth).

GET https://startup.jobs/feeds/jobs[?role=..&workplace=..]
Items: title "{Role} at {Company}", link, pubDate, description whose last line is the location.
Mechanism from career-ops providers/startup-jobs.mjs (MIT); code is our own.
"""
from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from urllib.parse import urlencode, urlsplit

from ._base import Context, Job, Provider, ProviderError, Target
from ._parse import feed_items, html_to_text, to_iso, workplace_from

HOST = "startup.jobs"
FEED = f"https://{HOST}/feeds/jobs"


class StartupJobs(Provider):
    name = "startup-jobs"
    wave = "W3"
    kind = "board"
    tenant = False
    hosts = (HOST,)

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        params = {}
        role = target.options.get("role") or target.query
        if role:
            params["role"] = role
        wp = target.options.get("workplace")
        if wp:
            params["workplace"] = wp
        url = FEED + ("?" + urlencode(params) if params else "")
        text = ctx.http.get_text(url)
        try:
            items = feed_items(text)
        except ET.ParseError as e:
            raise ProviderError(f"startup-jobs: bad feed: {e}") from e
        jobs: list[Job] = []
        for it in items:
            link = (it.get("link") or "").strip()
            p = urlsplit(link)
            if p.scheme != "https" or p.netloc != HOST:
                continue
            raw = it.get("title") or ""
            idx = raw.rfind(" at ")
            if idx == -1:
                continue
            title = raw[:idx].strip()
            company = re.sub(r"^bei\s+", "", raw[idx + 4:].strip(), flags=re.I)
            if not title or not company:
                continue
            lines = [l.strip() for l in html_to_text(it.get("description") or "").split("\n") if l.strip()]
            loc = lines[-1].split(" · ")[0].strip() if lines else ""
            jobs.append(self.job(
                title=title, url=f"https://{HOST}{p.path}", company=company, location=loc,
                workplace=workplace_from(loc),
                posted_at=to_iso(it.get("published")),
            ).validate())
            if len(jobs) >= ctx.max_jobs:
                break
        return jobs


PROVIDER = StartupJobs()
