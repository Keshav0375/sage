"""Jibe (iCIMS Jibe / jibeapply.com) — public ``/api/jobs`` JSON, paged with ?page=N.

Mechanism from career-ops providers/jibeapply.mjs (MIT). Job links use the careers site origin.
"""
from __future__ import annotations

import re
from urllib.parse import quote, urlencode, urlsplit, parse_qsl

from ._base import Context, Job, Provider, ProviderError, Target

MAX_PAGES = 50
DEFAULT_PAGE_SIZE = 10


def _api(raw: str) -> str:
    u = urlsplit(raw or "")
    if u.scheme != "https" or not re.fullmatch(r"[a-z0-9-]+\.jibeapply\.com", u.netloc.lower()):
        return ""
    path = u.path if u.path.startswith("/api/") else "/api" + (u.path if u.path.startswith("/") else "/" + u.path)
    return f"https://{u.netloc}{path}" + (f"?{u.query}" if u.query else "")


def _with(url: str, **kv) -> str:
    u = urlsplit(url)
    q = dict(parse_qsl(u.query))
    q.update({k: str(v) for k, v in kv.items()})
    return f"{u.scheme}://{u.netloc}{u.path}?{urlencode(q)}"


class JibeApply(Provider):
    name = "jibeapply"
    wave = "W2"
    kind = "ats"
    tenant = True
    hosts = ("jibeapply.com",)

    def detect(self, careers_url: str):
        api = _api(careers_url)
        if not api:
            return None
        return Target(slug=urlsplit(api).netloc.split(".")[0], careers_url=careers_url, api_url=api)

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        raw_api = target.api_url if str(target.api_url or "").startswith("https://") else ""
        api = raw_api or _api(target.careers_url)
        if not api:
            raise ProviderError("jibeapply needs a careers_url (or api_url)")
        o = urlsplit(target.careers_url or api)
        origin = f"{o.scheme}://{o.netloc}"
        first = ctx.http.get_json(api)
        if not isinstance(first, dict):
            raise ProviderError("jibeapply: unexpected response")
        items = list(first.get("jobs") or [])
        total = first.get("totalCount") or 0
        size = len(items) or first.get("count") or DEFAULT_PAGE_SIZE
        if total > size > 0:
            for page in range(2, min(-(-total // size), MAX_PAGES) + 1):
                if len(items) >= ctx.max_jobs:
                    break
                items.extend((ctx.http.get_json(_with(api, page=page)) or {}).get("jobs") or [])
        company = target.company
        jobs: list[Job] = []
        for it in items:
            d = (it or {}).get("data") or it or {}
            title = str(d.get("title") or "").strip()
            slug = d.get("slug") or d.get("req_id")
            if not title or not slug:
                continue
            loc = d.get("full_location") or ", ".join(str(x) for x in (d.get("city"), d.get("country")) if x)
            jobs.append(self.job(title=title, url=f"{origin}/jobs/{quote(str(slug), safe='')}",
                                 company=str(d.get("hiring_organization") or company or "").strip(), location=str(loc or ""),
                                 posted_at=str(d.get("posted_date") or d.get("create_date") or ""),
                                 department=str(d.get("category") or d.get("department") or ""),
                                 source_id=str(d.get("req_id") or slug)).validate())
            if len(jobs) >= ctx.max_jobs:
                break
        return jobs


PROVIDER = JibeApply()
