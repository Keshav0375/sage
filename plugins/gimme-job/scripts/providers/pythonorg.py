"""Python.org jobs board — public RSS feed (no auth).

GET https://www.python.org/jobs/feed/rss/ ; title "{Role}, {Company}", description's first line is the location.
Mechanism from career-ops providers/pythonorg.mjs (MIT); code is our own.
"""
from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from urllib.parse import urlsplit

from ._base import Context, Job, Provider, ProviderError, Target
from ._parse import feed_items, html_to_text, to_iso

FEED = "https://www.python.org/jobs/feed/rss/"


def _trusted(url: str) -> bool:
    p = urlsplit(url or "")
    h = p.netloc.lower()
    return p.scheme == "https" and (h == "python.org" or h.endswith(".python.org"))


class PythonOrg(Provider):
    name = "pythonorg"
    wave = "W3"
    kind = "board"
    tenant = False
    hosts = ("python.org",)

    def detect(self, careers_url: str):
        p = urlsplit(careers_url or "")
        if p.scheme == "https" and p.netloc.lower() in ("python.org", "www.python.org") and re.match(r"^/jobs(/|$)", p.path):
            return Target(careers_url=careers_url, api_url=FEED)
        return None

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        try:
            items = feed_items(ctx.http.get_text(FEED))
        except ET.ParseError as e:
            raise ProviderError(f"pythonorg: bad feed: {e}") from e
        jobs: list[Job] = []
        for it in items:
            link = (it.get("link") or it.get("id") or "").strip()
            raw = (it.get("title") or "").strip()
            if not _trusted(link) or "," not in raw:
                continue
            role, _, company = raw.rpartition(",")
            role, company = role.strip(), company.strip()
            if not role or not company:
                continue
            desc = it.get("description") or ""
            loc = ""
            if desc:
                chunk = re.split(r"\r?\n|(?=<[a-z/!])|(?=&lt;[a-z/!])", desc, flags=re.I)[0]
                if not re.match(r"^\s*(?:<|&lt;)", chunk, re.I):
                    loc = html_to_text(chunk)
            jobs.append(self.job(
                title=role, url=link, company=company, location=loc,
                posted_at=to_iso(it.get("published")), description=html_to_text(desc),
            ).validate())
            if len(jobs) >= ctx.max_jobs:
                break
        return jobs


PROVIDER = PythonOrg()
