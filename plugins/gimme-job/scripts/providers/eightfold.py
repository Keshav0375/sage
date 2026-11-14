"""Eightfold careers — GET /api/apply/v2/jobs (falls back to /api/pcsx/search on 403).

Mechanism from career-ops providers/eightfold.mjs (MIT). Branded hosts: pass target.options["eightfold_host"].
"""
from __future__ import annotations

import re
from urllib.parse import parse_qs, urlencode, urlsplit

from ._base import Context, Job, Provider, ProviderError, Target
from ._parse import to_iso

HOST_RE = re.compile(r"^[a-z0-9-]+\.eightfold\.ai$", re.I)
PAGE_SIZE = 10
MAX_PAGES = 200


def _tenant(target: Target):
    branded = str(target.options.get("eightfold_host") or "").strip().lower()
    for raw in (target.api_url, target.careers_url):
        p = urlsplit(raw or "")
        host = p.netloc.lower()
        if p.scheme != "https" or not (HOST_RE.match(host) or (branded and host == branded)):
            continue
        dom = target.options.get("domain") or (parse_qs(p.query).get("domain") or [""])[0].strip()
        return {"host": host, "domain": dom}
    return None


def _url(t, path: str, start: int, num: int | None = None) -> str:
    q = {}
    if t["domain"]:
        q["domain"] = t["domain"]
    q["start"] = str(start)
    if num:
        q["num"] = str(num)
    return f"https://{t['host']}{path}?{urlencode(q)}"


def _ts(v) -> str:
    try:
        n = float(v)
    except (TypeError, ValueError):
        return ""
    return to_iso(n) if n > 0 else ""


class Eightfold(Provider):
    name = "eightfold"
    wave = "W2"
    kind = "ats"
    tenant = True
    hosts = ("eightfold.ai",)

    def detect(self, careers_url: str):
        t = _tenant(Target(careers_url=careers_url))
        if not t:
            return None
        return Target(slug=t["host"].split(".")[0], careers_url=careers_url, api_url=_url(t, "/api/apply/v2/jobs", 0, PAGE_SIZE))

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        t = _tenant(target)
        if not t:
            raise ProviderError("eightfold needs an https *.eightfold.ai url (or options.eightfold_host)")
        company = target.company or t["host"].split(".")[0]
        api = "v2"
        jobs: list[Job] = []
        total = None
        for page in range(MAX_PAGES):
            start = page * PAGE_SIZE
            if api == "v2":
                try:
                    data = ctx.http.get_json(_url(t, "/api/apply/v2/jobs", start, PAGE_SIZE))
                except ProviderError as e:
                    if page == 0 and "403" in str(e):
                        api = "pcsx"
                    else:
                        raise
            if api == "pcsx":
                raw = ctx.http.get_json(_url(t, "/api/pcsx/search", start))
                d = (raw or {}).get("data") or {}
                if not isinstance(d.get("positions"), list):
                    raise ProviderError("eightfold: unrecognized /api/pcsx/search body")
                data = {"positions": [dict(p, t_create=p.get("t_create") or p.get("postedTs") or p.get("creationTs"),
                                           ats_job_id=p.get("ats_job_id") or p.get("atsJobId") or p.get("displayJobId"))
                                      for p in d["positions"]], "count": d.get("count")}
            positions = (data or {}).get("positions") or []
            for p in positions:
                title = (p.get("name") or p.get("posting_name") or "").strip()
                pid = str(p.get("id") or p.get("position_id") or "")
                url = (p.get("canonicalPositionUrl") or "").strip()
                if not url.startswith("https://") and pid:
                    q = {"pid": pid}
                    if t["domain"]:
                        q["domain"] = t["domain"]
                    url = f"https://{t['host']}/careers?{urlencode(q)}"
                locs = list(dict.fromkeys(x.strip() for x in ([p.get("location")] + list(p.get("locations") or [])) if isinstance(x, str) and x.strip()))
                jobs.append(self.job(title=title, url=url, company=company, locations=locs, location=" · ".join(locs),
                                     posted_at=_ts(p.get("t_create")) or _ts(p.get("t_update")),
                                     department=p.get("department") or "", source_id=pid,
                                     extra={"requisition_id": str(p.get("ats_job_id") or "")} if p.get("ats_job_id") else {}).validate())
                if len(jobs) >= ctx.max_jobs:
                    return jobs
            if total is None and isinstance((data or {}).get("count"), (int, float)):
                total = data["count"]
            if len(positions) < PAGE_SIZE or (total is not None and start + PAGE_SIZE >= total):
                break
        return jobs


PROVIDER = Eightfold()
