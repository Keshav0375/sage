"""Workday — CXS public jobs endpoint (no auth).

POST https://{tenant}.{wdN}.myworkdayjobs.com/wday/cxs/{tenant}/{site}/jobs
Mechanism from career-ops providers/workday.mjs (MIT); code is our own.
Simplified: no facet-splitting for the offset ceiling, no detail enrichment.
"""
from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from urllib.parse import unquote

from ._base import Context, Job, Provider, ProviderError, Target

PAGE = 20
_CAREERS = re.compile(r"^https://([\w-]+)\.(wd[\w-]*)\.myworkdayjobs\.com/(?:[a-z]{2}-[A-Z]{2}/)?([^/?#]+)")
_CXS = re.compile(r"^https://([\w-]+)\.(wd[\w-]*)\.myworkdayjobs\.com/wday/cxs/([\w-]+)/([^/?#]+)")
_SITE = re.compile(r"^https://([\w-]+)\.myworkdaysite\.com/recruiting/([\w-]+)/([^/?#]+)")


def _endpoint(url: str):
    """-> (api, job_base) or None."""
    m = _CXS.match(url or "")
    if m:
        host, inst, ten, site = m.groups()
        o = f"https://{host}.{inst}.myworkdayjobs.com"
        return f"{o}/wday/cxs/{ten}/{site}/jobs", f"{o}/{site}"
    m = _SITE.match(url or "")
    if m:
        inst, ten, site = m.groups()
        o = f"https://{inst}.myworkdaysite.com"
        return f"{o}/wday/cxs/{ten}/{site}/jobs", f"{o}/recruiting/{ten}/{site}"
    m = _CAREERS.match(url or "")
    if m:
        ten, inst, site = m.groups()
        o = f"https://{ten}.{inst}.myworkdayjobs.com"
        return f"{o}/wday/cxs/{ten}/{site}/jobs", f"{o}/{site}"
    return None


def _posted(label: str) -> str:
    if not label:
        return ""
    now = datetime.now(timezone.utc)
    t = label.lower()
    if "today" in t:
        return now.date().isoformat()
    if "yesterday" in t:
        return (now - timedelta(days=1)).date().isoformat()
    m = re.search(r"posted\s+(\d+)(\+?)\s*day", t)
    if m and not m.group(2):
        return (now - timedelta(days=int(m.group(1)))).date().isoformat()
    return ""


class Workday(Provider):
    name = "workday"
    wave = "W1"
    kind = "ats"
    tenant = True
    hosts = ("myworkdayjobs.com", "myworkdaysite.com")

    def detect(self, careers_url: str):
        ep = _endpoint(careers_url)
        return Target(careers_url=careers_url, api_url=ep[0]) if ep else None

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        ep = _endpoint(target.api_url) or _endpoint(target.careers_url)
        if not ep:
            raise ProviderError("workday: cannot derive CXS endpoint")
        api, base = ep
        origin = api.split("/wday/")[0]
        hdrs = {"Origin": origin, "Referer": base + "/", "Accept": "application/json"}
        out: list[Job] = []
        offset, total = 0, None
        while len(out) < ctx.max_jobs:
            data = ctx.http.post_json(api, {"limit": PAGE, "offset": offset, "searchText": "", "appliedFacets": {}},
                                      headers=hdrs)
            rows = data.get("jobPostings") if isinstance(data, dict) else None
            if not isinstance(rows, list):
                raise ProviderError("workday: expected jobPostings[]")
            if total is None and isinstance(data.get("total"), int):
                total = data["total"]
            for j in rows:
                path = j.get("externalPath") or ""
                if not path or not str(j.get("title", "")).strip():
                    continue
                m = re.search(r"/job/([^/]+)/", path)
                loc = j.get("locationsText") or (unquote(m.group(1)).replace("-", " ") if m else "")
                if str(j.get("remoteType", "")).lower().startswith("fully") and "remote" not in loc.lower():
                    loc = f"{loc} (Remote)".strip()
                bullets = j.get("bulletFields") or []
                out.append(self.job(
                    title=j["title"], url=base + path,
                    company=target.company, location=loc,
                    workplace="remote" if str(j.get("remoteType", "")).lower().startswith("fully") else "",
                    posted_at=_posted(j.get("postedOn", "")),
                    source_id=str(bullets[0]) if bullets else path.rstrip("/").rsplit("_", 1)[-1],
                ).validate())
            offset += PAGE
            if len(rows) < PAGE or (total is not None and offset >= total):
                break
        return out[: ctx.max_jobs]


PROVIDER = Workday()
