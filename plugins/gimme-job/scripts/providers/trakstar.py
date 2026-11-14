"""Trakstar Hire (ex-Recruiterbox) — https://jsapi.recruiterbox.com/v1/openings?client_name=<client>.

Mechanism from career-ops providers/trakstar.mjs (MIT); code is our own.
"""
from __future__ import annotations

import re
from urllib.parse import parse_qs, urlsplit

from ._base import Context, Job, Provider, ProviderError, Target
from ._parse import html_to_text

API_HOST = "jsapi.recruiterbox.com"
HIRE = ".hire.trakstar.com"
LEGACY = ".recruiterbox.com"
RESERVED = {"www", "jsapi", "api", "app", "mail", "support", "help", "status", "blog", "docs"}
SLUG = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$")
PAGE_SIZE = 100
MAX_PAGES = 20


def _client(url: str) -> str:
    p = urlsplit((url or "").strip())
    if p.scheme != "https":
        return ""
    host = (p.hostname or "").lower()
    cand = ""
    if host == API_HOST:
        if not re.match(r"^/v1/openings/?$", p.path):
            return ""
        cand = (parse_qs(p.query).get("client_name") or [""])[0]
    elif host.endswith(HIRE):
        cand = host[: -len(HIRE)]
    elif host.endswith(LEGACY):
        cand = host[: -len(LEGACY)]
    cand = cand.lower()
    if not cand or "." in cand or cand in RESERVED or not SLUG.match(cand):
        return ""
    return cand


def _t(v) -> str:
    return v.strip() if isinstance(v, str) else ""


class Trakstar(Provider):
    name = "trakstar"
    wave = "W4"
    kind = "ats"
    tenant = True
    hosts = ("trakstar.com", "recruiterbox.com")

    def detect(self, careers_url: str):
        c = _client(careers_url)
        if not c:
            return None
        return Target(slug=c, careers_url=careers_url, api_url=f"https://{API_HOST}/v1/openings?client_name={c}")

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        c = target.slug or _client(target.api_url) or _client(target.careers_url)
        if not c:
            raise ProviderError("trakstar needs https://<client>.hire.trakstar.com")
        jobs: list[Job] = []
        seen: set[str] = set()
        offset = 0
        for _ in range(MAX_PAGES):
            data = ctx.http.get_json(f"https://{API_HOST}/v1/openings?client_name={c}&limit={PAGE_SIZE}&offset={offset}")
            rows = data.get("objects") if isinstance(data, dict) else None
            if not isinstance(rows, list):
                raise ProviderError("trakstar: unexpected response, expected objects[]")
            for r in rows:
                if not isinstance(r, dict):
                    continue
                title = re.sub(r"\s+", " ", r.get("title") or "").strip() if isinstance(r.get("title"), str) else ""
                url = ""
                hu = _t(r.get("hosted_url"))
                if hu:
                    u = urlsplit(hu)
                    if u.scheme == "https" and (u.hostname or "").lower() in (f"{c}{HIRE}", f"{c}{LEGACY}"):
                        url = hu
                if not url and r.get("id") not in (None, ""):
                    url = f"https://{c}{HIRE}/jobs/{r['id']}/"
                if not title or not url or url in seen:
                    continue
                seen.add(url)
                loc = r.get("location") if isinstance(r.get("location"), dict) else {}
                place = ", ".join(x for x in (_t(loc.get("city")), _t(loc.get("state")), _t(loc.get("country"))) if x)
                remote = r.get("allows_remote") is True
                location = (f"Remote ({place})" if place else "Remote") if remote else place
                jobs.append(self.job(
                    title=title, url=url, company=target.company or c, location=location,
                    workplace="remote" if remote else "",
                    description=html_to_text(r["description"]) if isinstance(r.get("description"), str) else "",
                    source_id=str(r.get("id", "")),
                ).validate())
                if len(jobs) >= ctx.max_jobs:
                    return jobs
            meta = data.get("meta") or {}
            total = meta.get("total") if isinstance(meta.get("total"), int) else meta.get("total_count")
            offset += len(rows)
            if len(rows) < PAGE_SIZE or (isinstance(total, int) and offset >= total):
                break
        return jobs


PROVIDER = Trakstar()
