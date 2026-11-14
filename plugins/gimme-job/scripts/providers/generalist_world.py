"""Generalist World — server-rendered jobs board (gw-job-card anchors).

GET https://generalist.world/jobs/ ; cards: <a class="gw-job-card" href="/jobs/{slug}/" data-region="..">
with gw-job-title / gw-job-company divs, gw-location span, gw-job-description paragraph.
Mechanism from career-ops providers/generalist-world.mjs (MIT); code is our own.
"""
from __future__ import annotations

import re

from ._base import Context, Job, Provider, ProviderError, Target
from ._parse import html_to_text

SITE = "https://generalist.world"
LIST_URL = SITE + "/jobs/"
CARD_RE = re.compile(r'<a(\s(?:[^>]*?\s)?class="(?:[^"]*\s)?gw-job-card(?:\s[^"]*)?"[^>]*)>(.*?)</a>', re.S)
HREF_RE = re.compile(r'\shref="([^"]*)"')
REGION_RE = re.compile(r'\sdata-region="([^"]*)"')
SLUG_RE = re.compile(r"^/jobs/([A-Za-z0-9][A-Za-z0-9._~-]*)/?$")


def _field(tag: str, cls: str, inner: str) -> str:
    m = re.search(rf'<{tag}\s(?:[^>]*?\s)?class="(?:[^"]*\s)?{cls}(?:\s[^"]*)?"[^>]*>(.*?)</{tag}>', inner, re.S)
    return html_to_text(m.group(1)) if m else ""


class GeneralistWorld(Provider):
    name = "generalist-world"
    wave = "W3"
    kind = "board"
    tenant = False
    hosts = ("generalist.world",)

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        html = ctx.http.get_text(LIST_URL)
        html = re.sub(r"<!--.*?-->|<(script|style|template|textarea)\b.*?</\1\s*>", " ", html, flags=re.S | re.I)
        jobs: list[Job] = []
        seen: set[str] = set()
        cards = 0
        for m in CARD_RE.finditer(html):
            cards += 1
            attrs, inner = m.group(1), m.group(2)
            hm = HREF_RE.search(attrs)
            href = (hm.group(1) if hm else "").strip()
            href = re.sub(r"^https://(www\.)?generalist\.world", "", href)
            sm = SLUG_RE.match(href)
            if not sm:
                continue
            url = f"{SITE}/jobs/{sm.group(1)}/"
            title, company = _field("div", "gw-job-title", inner), _field("div", "gw-job-company", inner)
            if not title or not company or url in seen:
                continue
            seen.add(url)
            loc = _field("span", "gw-location", inner)
            if not loc:
                rm = REGION_RE.search(attrs)
                code = (rm.group(1) if rm else "").strip().lower()
                loc = "Remote" if code == "remote" else re.sub(r"[-_]+", " ", code).upper()
            jobs.append(self.job(
                title=title, url=url, company=company, location=loc,
                workplace="remote" if loc.lower() == "remote" else "",
                description=_field("p", "gw-job-description", inner), source_id=sm.group(1),
            ).validate())
            if len(jobs) >= ctx.max_jobs:
                break
        if not jobs and cards:
            raise ProviderError("generalist-world: cards matched but none usable; markup changed")
        return jobs


PROVIDER = GeneralistWorld()
