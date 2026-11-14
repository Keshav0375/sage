"""HiBob careers sites — GET https://<tenant>.careers.hibob.com/api/job-ad (header companyidentifier).

Mechanism from career-ops providers/hibob.mjs (MIT); code is our own.
"""
from __future__ import annotations

import re
from urllib.parse import urlsplit

from ._base import Context, Job, Provider, ProviderError, Target
from ._parse import html_to_text, to_iso

SUFFIX = ".careers.hibob.com"
LABEL = re.compile(r"^[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$")


def _tenant(url: str) -> str:
    p = urlsplit((url or "").strip())
    host = (p.hostname or "").lower()
    if p.scheme != "https" or not host.endswith(SUFFIX):
        return ""
    t = host[: -len(SUFFIX)]
    return t if LABEL.match(t) else ""


def _s(v) -> str:
    return v.strip() if isinstance(v, str) else ""


def _amount(v):
    try:
        n = float(v)
    except (TypeError, ValueError):
        return None
    return n if n > 0 else None


class HiBob(Provider):
    name = "hibob"
    wave = "W4"
    kind = "ats"
    tenant = True
    hosts = ("careers.hibob.com",)

    def detect(self, careers_url: str):
        t = _tenant(careers_url)
        if not t:
            return None
        return Target(slug=t, careers_url=careers_url, api_url=f"https://{t}{SUFFIX}/api/job-ad")

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        t = target.slug or _tenant(target.careers_url) or _tenant(target.api_url)
        if not t:
            raise ProviderError("hibob needs https://<tenant>.careers.hibob.com")
        origin = f"https://{t}{SUFFIX}"
        data = ctx.http.get_json(f"{origin}/api/job-ad",
                                 headers={"Accept": "application/json", "companyidentifier": t})
        rows = (data or {}).get("jobAdDetails") if isinstance(data, dict) else None
        if not isinstance(rows, list):
            raise ProviderError("hibob: unexpected response, expected jobAdDetails[]")
        jobs: list[Job] = []
        for r in rows[: ctx.max_jobs]:
            if not isinstance(r, dict) or not _s(r.get("title")) or not _s(r.get("id")):
                continue
            site, country = _s(r.get("site")), _s(r.get("country"))
            parts = [site]
            if country and country.lower() not in site.lower():
                parts.append(country)
            workplace = "remote" if _s(r.get("workspaceTypeId")) == "remote" else ""
            if workplace and not re.search(r"\bremote\b", site, re.I):
                parts.append("Remote")
            kw = {}
            if _s(r.get("payTransparencySalaryPayPeriod")).lower() == "annual":
                lo, hi = _amount(r.get("payTransparencyMinSalary")), _amount(r.get("payTransparencyMaxSalary"))
                if lo or hi:
                    lo, hi = lo or hi, hi or lo
                    kw = dict(salary_min=min(lo, hi), salary_max=max(lo, hi), salary_period="year",
                              currency=_s(r.get("payTransparencySalaryCurrency")).upper())
            desc = "<br>".join(r[k] for k in ("description", "responsibilities", "requirements", "benefits")
                               if isinstance(r.get(k), str) and r[k])
            jobs.append(self.job(
                title=r["title"], url=f"{origin}/jobs/{_s(r['id'])}",
                company=target.company or t, location=", ".join(x for x in parts if x),
                workplace=workplace, posted_at=to_iso(r.get("publishedAt")),
                description=html_to_text(desc), source_id=_s(r["id"]), **kw,
            ).validate())
        return jobs


PROVIDER = HiBob()
