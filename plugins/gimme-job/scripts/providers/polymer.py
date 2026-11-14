"""Polymer — public API: api.polymer.co/v1/hire/organizations/<slug>/jobs?page=N.

Mechanism from career-ops providers/polymer.mjs (MIT).
"""
from __future__ import annotations

import re
from urllib.parse import quote, unquote, urlsplit

from ._base import Context, Job, Provider, ProviderError, Target
from ._parse import to_iso

SLUG_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$")
MAX_PAGES = 20


def _slug(url: str) -> str:
    p = urlsplit((url or "").strip())
    if p.scheme != "https":
        return ""
    host = p.netloc.lower()
    cand = ""
    if host == "jobs.polymer.co":
        segs = [s for s in p.path.split("/") if s]
        cand = segs[0] if segs else ""
    elif host == "api.polymer.co":
        m = re.match(r"^/v1/hire/organizations/([^/]+)", p.path)
        cand = m.group(1) if m else ""
    cand = unquote(cand).lower()
    return cand if SLUG_RE.match(cand) else ""


def _place(r: dict) -> str:
    d = str(r.get("display_location") or "").strip()
    if d:
        return d
    place = ", ".join(str(r.get(k)).strip() for k in ("city", "state_region", "country") if r.get(k) and str(r.get(k)).strip())
    rem = str(r.get("remoteness_pretty") or "")
    if rem and not re.match(r"(?i)no\s+remote\b", rem) and re.search(r"(?i)\bremote\b", rem):
        return f"Remote ({place})" if place else "Remote"
    return place


class Polymer(Provider):
    name = "polymer"
    wave = "W2"
    kind = "ats"
    tenant = True
    hosts = ("polymer.co",)

    def detect(self, careers_url: str):
        s = _slug(careers_url)
        if not s:
            return None
        return Target(slug=s, careers_url=careers_url, api_url=f"https://api.polymer.co/v1/hire/organizations/{s}/jobs")

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        slug = _slug(target.api_url) or _slug(target.careers_url) or target.slug
        if not slug:
            raise ProviderError("polymer needs a jobs.polymer.co/<slug> url")
        jobs: list[Job] = []
        seen: set[str] = set()
        prev_key = None
        for page in range(1, MAX_PAGES + 1):
            data = ctx.http.get_json(f"https://api.polymer.co/v1/hire/organizations/{slug}/jobs?page={page}")
            rows = data.get("items") if isinstance(data, dict) else None
            if not isinstance(rows, list):
                raise ProviderError("polymer: expected items[]")
            meta = data.get("meta") or {}
            key = [r.get("id") for r in rows if isinstance(r, dict)]
            for r in rows:
                if not isinstance(r, dict):
                    continue
                title = " ".join(str(r.get("title") or "").split())
                url = str(r.get("job_post_url") or "").strip()
                if not url.startswith("https://jobs.polymer.co"):
                    jid = r.get("id") or r.get("job_id")
                    url = f"https://jobs.polymer.co/{slug}/{quote(str(jid), safe='')}" if jid not in (None, "") else ""
                if not title or not url or url in seen:
                    continue
                seen.add(url)
                ts = r.get("published_at") or r.get("published_at_timestamp")
                jobs.append(self.job(title=title, url=url, company=target.company or slug, location=_place(r),
                                     posted_at=to_iso(ts), source_id=str(r.get("id") or "")).validate())
                if len(jobs) >= ctx.max_jobs:
                    return jobs
            if not rows or key == prev_key or meta.get("is_last") is True:
                break
            prev_key = key
        return jobs


PROVIDER = Polymer()
