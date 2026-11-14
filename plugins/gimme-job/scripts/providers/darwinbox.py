"""Darwinbox — POST <tenant>.darwinbox.(in|com)/ms/candidateapi/job/alljobs?companyId=<id>.

Mechanism from career-ops providers/darwinbox.mjs (MIT); code is our own.
"""
from __future__ import annotations

import html as htmllib
import re
from urllib.parse import urlsplit

from ._base import Context, Job, Provider, ProviderError, Target
from ._parse import html_to_text, to_iso

HOST = re.compile(r"^[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.darwinbox\.(?:in|com)$")
PATH = re.compile(r"^/ms/candidatev2/([a-z0-9_-]+)/careers(?:/|$)", re.I)
PAGE_SIZE = 50
MAX_PAGES = 20


def _board(url: str):
    p = urlsplit((url or "").strip())
    host = (p.hostname or "").lower()
    if p.scheme != "https" or not HOST.match(host):
        return None
    m = PATH.match(p.path)
    return (f"https://{host}", m.group(1)) if m else None


def _clean(v) -> str:
    return re.sub(r"\s+", " ", htmllib.unescape(v)).strip() if isinstance(v, str) else ""


def _amount(v):
    try:
        n = float(v)
    except (TypeError, ValueError):
        return None
    return n if n > 0 else None


class Darwinbox(Provider):
    name = "darwinbox"
    wave = "W4"
    kind = "ats"
    tenant = True
    hosts = ("darwinbox.in", "darwinbox.com")

    def detect(self, careers_url: str):
        b = _board(careers_url)
        if not b:
            return None
        return Target(slug=b[1], careers_url=careers_url,
                      api_url=f"{b[0]}/ms/candidatev2/{b[1]}/careers/allJobs")

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        b = _board(target.careers_url) or _board(target.api_url)
        if not b:
            raise ProviderError("darwinbox needs https://<tenant>.darwinbox.in/ms/candidatev2/<companyId>/careers/allJobs")
        origin, cid = b
        endpoint = f"{origin}/ms/candidateapi/job/alljobs?companyId={cid}"
        company = target.company or urlsplit(origin).hostname.split(".")[0]
        jobs: list[Job] = []
        seen: set[str] = set()
        for page in range(1, MAX_PAGES + 1):
            data = ctx.http.post_json(endpoint, {"companyId": cid, "page": page, "sort_option": "new", "limit": PAGE_SIZE})
            rows = data.get("data") if isinstance(data, dict) and data.get("status") == "success" else None
            if not isinstance(rows, list):
                raise ProviderError("darwinbox: unexpected response, expected status success and a data array")
            for r in rows:
                if not isinstance(r, dict):
                    continue
                title = _clean(r.get("title"))
                jid = str(r.get("id") or "").strip()
                if not title or not jid:
                    continue
                url = f"{origin}/ms/candidatev2/{cid}/careers/jobDetails/{jid}"
                if url in seen:
                    continue
                seen.add(url)
                tips = r.get("tool_tip_locations") if isinstance(r.get("tool_tip_locations"), list) else []
                parts: list[str] = []
                for loc in (tips or [r.get("locations")]):
                    lab = _clean(loc).replace(" ,", ",") if isinstance(loc, str) else ""
                    if lab and lab not in parts:
                        parts.append(lab)
                posted = r.get("posted_on")
                posted = posted if isinstance(posted, (int, float)) and posted > 0 else r.get("created_on")
                kw = {}
                if str(r.get("salary_timeframe") or "").strip().lower() == "annual":
                    lo, hi = _amount(r.get("salary_min")), _amount(r.get("salary_max"))
                    if lo or hi:
                        lo, hi = lo or hi, hi or lo
                        kw = dict(salary_min=min(lo, hi), salary_max=max(lo, hi), salary_period="year",
                                  currency=str(r.get("salary_currency") or "").strip().upper())
                jobs.append(self.job(
                    title=title, url=url, company=company, location="; ".join(parts),
                    posted_at=to_iso(posted), description=html_to_text(r.get("jd") or ""),
                    source_id=jid, **kw,
                ).validate())
                if len(jobs) >= ctx.max_jobs:
                    return jobs
            if len(rows) < PAGE_SIZE:
                break
        return jobs


PROVIDER = Darwinbox()
