"""BWI GmbH — job URLs from the careers listing page; titles derived from the URL slug.

Mechanism from career-ops providers/bwi.mjs (MIT); code is our own. The optional per-posting
JSON-LD enrichment is skipped (list-only: titles come from slugs).
"""
from __future__ import annotations

import re
from urllib.parse import urlsplit

from ._base import Context, Job, Provider, Target

LIST_URL = "https://www.bwi.de/karriere/stellenangebote"
HOST = "www.bwi.de"
JOB_URL_RE = re.compile(r'"url":\s*"(https://www\.bwi\.de/karriere/stellenangebote/job/[^"]+)"')
GENDER_TAIL = re.compile(r"-(?:m-w-d|m-d-w|w-m-d|d-m-w)-?\d{4,6}$", re.I)
SLUG_TAIL = re.compile(r"-(?:m-w-d|m-d-w|w-m-d|d-m-w)?-?\d{4,6}$", re.I)


def slug_to_title(url: str) -> str:
    slug = urlsplit(url).path.rstrip("/").split("/")[-1]
    core = SLUG_TAIL.sub("", slug)
    if not core:
        return ""
    words = [w[:1].upper() + w[1:] for w in core.split("-") if w]
    return " ".join(words) + (" (m/w/d)" if GENDER_TAIL.search(slug) else "")


class Bwi(Provider):
    name = "bwi"
    wave = "W6"
    kind = "company"
    tenant = False
    hosts = (HOST,)

    def detect(self, careers_url: str):
        if urlsplit(careers_url or "").netloc.lower() == HOST:
            return Target(careers_url=LIST_URL)
        return None

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        html = ctx.http.get_text(LIST_URL)
        jobs, seen = [], set()
        for url in JOB_URL_RE.findall(html):
            if url in seen:
                continue
            seen.add(url)
            title = slug_to_title(url)
            if not title:
                continue
            jobs.append(self.job(title=title, url=url, company=target.company or "BWI",
                                 source_id=url.rsplit("-", 1)[-1]).validate())
            if len(jobs) >= ctx.max_jobs:
                break
        return jobs


PROVIDER = Bwi()
