"""CryptocurrencyJobs — public RSS feed (no auth).

GET https://cryptocurrencyjobs.co/index.xml ; title "Role at Company"; description teaser carries a
"This is a full-time position that <clause>" sentence that we map to a location.
Mechanism from career-ops providers/cryptocurrencyjobs.mjs (MIT); code is our own.
"""
from __future__ import annotations

import html
import re
import xml.etree.ElementTree as ET

from ._base import Context, Job, Provider, ProviderError, Target
from ._parse import feed_items, to_iso

FEED = "https://cryptocurrencyjobs.co/index.xml"


def _places(s: str) -> list[str]:
    parts = re.split(r"\s*,\s*(?:or\s+)?|\s+or\s+", s, flags=re.I)
    return [re.sub(r"^the\s+", "", p.strip(), flags=re.I) for p in parts if p.strip()]


def _city(place: str) -> str:
    return re.sub(r"^(.*\S)\s+([A-Z]{2})$", r"\1, \2", place)


def teaser_clause(teaser: str) -> str:
    m = re.search(r"\bThis is an? [\w-]+(?: [\w-]+)? position that\s+(.+?)\s*\.?\s*$", teaser or "", re.I | re.S)
    return re.sub(r"\s+", " ", m.group(1)).strip() if m else ""


def location_from_clause(clause: str) -> str:
    c = re.sub(r"\.\s*Work remotely from anywhere\.?$", "", clause or "", flags=re.I).strip()
    if re.fullmatch(r"is 100% remote with no geographical restrictions", c, re.I):
        return "Remote (worldwide)"
    m = re.match(r"^(is remote or )?(?:is |can be )?based in (.+)$", c, re.I)
    if m:
        places = [_city(p) for p in _places(m.group(2))]
        return "; ".join((["Remote"] if m.group(1) else []) + places)
    m = re.match(r"^can be done remotely anywhere in (.+?)(?: or on-site in (.+))?$", c, re.I)
    if m:
        regions = _places(m.group(1))
        if not regions:
            return ""
        onsite = [_city(p) for p in _places(m.group(2))] if m.group(2) else []
        return "; ".join([f"Remote ({', '.join(regions)})"] + onsite)
    return ""


class CryptocurrencyJobs(Provider):
    name = "cryptocurrencyjobs"
    wave = "W3"
    kind = "board"
    tenant = False
    hosts = ("cryptocurrencyjobs.co",)

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        try:
            items = feed_items(ctx.http.get_text(FEED))
        except ET.ParseError as e:
            raise ProviderError(f"cryptocurrencyjobs: bad feed: {e}") from e
        jobs: list[Job] = []
        for it in items:
            raw = html.unescape(it.get("title") or "").strip()
            link = (it.get("link") or it.get("id") or "").strip()
            if not raw or not link:
                continue
            idx = raw.rfind(" at ")
            title, company = (raw[:idx].strip(), raw[idx + 4:].strip()) if idx > 0 else (raw, "")
            desc = html.unescape(html.unescape(it.get("description") or ""))
            loc = location_from_clause(teaser_clause(desc))
            jobs.append(self.job(
                title=title, url=link, company=company, location=loc,
                workplace="remote" if loc.startswith("Remote") and ";" not in loc else "",
                posted_at=to_iso(it.get("published")),
            ).validate())
            if len(jobs) >= ctx.max_jobs:
                break
        return jobs


PROVIDER = CryptocurrencyJobs()
