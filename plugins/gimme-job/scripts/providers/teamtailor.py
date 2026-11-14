"""Teamtailor — public jobs RSS feed (no auth).

GET https://{slug}.teamtailor.com/jobs.rss
Mechanism from career-ops providers/teamtailor.mjs (MIT); code is our own.
"""
from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from urllib.parse import urlsplit

from ._base import Context, Job, Provider, ProviderError, Target
from ._parse import html_to_text, to_iso

HOST_RE = re.compile(r"^([a-z0-9](?:[a-z0-9-]*[a-z0-9])?)\.teamtailor\.com$", re.I)


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


class Teamtailor(Provider):
    name = "teamtailor"
    wave = "W1"
    kind = "ats"
    tenant = True
    hosts = ("teamtailor.com",)

    def detect(self, careers_url: str):
        host = urlsplit(careers_url or "").netloc.lower()
        m = HOST_RE.match(host)
        if not m or m.group(1) in ("www", "app", "career"):
            return None
        return Target(slug=m.group(1), careers_url=careers_url, api_url=f"https://{host}/jobs.rss")

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        t = target if target.api_url else (self.detect(target.careers_url) or target)
        feed = t.api_url or (f"https://{t.slug}.teamtailor.com/jobs.rss" if t.slug else "")
        if not feed:
            raise ProviderError("teamtailor needs a slug or teamtailor.com url")
        try:
            root = ET.fromstring(ctx.http.get_text(feed).lstrip("﻿").strip())
        except ET.ParseError as e:
            raise ProviderError(f"teamtailor: bad feed: {e}") from e
        jobs: list[Job] = []
        for item in root.iter("item"):
            f: dict[str, str] = {}
            for c in item.iter():
                if c is not item:
                    f.setdefault(_local(c.tag), (c.text or "").strip())
            url, title = f.get("link", ""), f.get("title", "")
            if not url.startswith("https://") or not title:
                continue
            place = ", ".join(x for x in (f.get("city"), f.get("country")) if x)
            remote = f.get("remoteStatus", "").lower()
            if not place and remote in ("fully", "temporary"):
                place = "Remote"
            jobs.append(self.job(
                title=title, url=url, company=target.company or t.slug, location=place,
                workplace="remote" if remote in ("fully", "temporary") else ("hybrid" if remote == "hybrid" else ""),
                department=f.get("department", ""), posted_at=to_iso(f.get("pubDate")),
                description=html_to_text(f.get("description", "")), source_id=f.get("guid", ""),
            ).validate())
            if len(jobs) >= ctx.max_jobs:
                break
        return jobs


PROVIDER = Teamtailor()
