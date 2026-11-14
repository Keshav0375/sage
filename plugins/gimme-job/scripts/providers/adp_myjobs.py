"""ADP MyJobs — public staffing API at myjobs.adp.com/public/staffing/v1 (orgoid resolved from the career-site slug).

Mechanism from career-ops providers/adp-myjobs.mjs (MIT); list path only.
"""
from __future__ import annotations

import re
from urllib.parse import quote, urlsplit

from ._base import Context, Job, Provider, ProviderError, Target

HOST = "myjobs.adp.com"
API = f"https://{HOST}/public/staffing/v1"
PAGE_SIZE = 200
MAX_PAGES = 100
SITE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")
ORGOID_RE = re.compile(r"^[A-Za-z0-9]{8,64}$")
RESERVED = {"public", "admin", "myadp_prefix"}


def _site(url: str) -> str:
    p = urlsplit(url or "")
    if p.scheme != "https" or p.netloc.lower() != HOST:
        return ""
    segs = [s for s in p.path.split("/") if s]
    seg = segs[0] if segs else ""
    return seg if seg and SITE_RE.match(seg) and seg.lower() not in RESERVED else ""


def _s(v) -> str:
    return v.strip() if isinstance(v, str) else ""


def _location(row: dict) -> str:
    out: list[str] = []
    for loc in row.get("requisitionLocations") or []:
        a = (loc or {}).get("address") or {}
        sub = a.get("countrySubdivisionLevel1") or {}
        code = _s(sub.get("codeValue"))
        region = code if re.fullmatch(r"[A-Za-z]{2,3}", code) else (_s(sub.get("longName")) or code)
        country = _s((a.get("country") or {}).get("codeValue")) or _s((a.get("country") or {}).get("longName"))
        label = ", ".join(x for x in (_s(a.get("cityName")), region, country) if x)
        if not label:
            nc = (loc or {}).get("nameCode") or {}
            label = _s(nc.get("longName")) or _s(nc.get("shortName"))
        if label and label not in out:
            out.append(label)
    return " / ".join(out)


class AdpMyJobs(Provider):
    name = "adp-myjobs"
    wave = "W2"
    kind = "ats"
    tenant = True
    hosts = (HOST,)

    def detect(self, careers_url: str):
        s = _site(careers_url)
        if not s:
            return None
        return Target(slug=s, careers_url=careers_url, api_url=f"{API}/job-requisitions?rb=CareerSite")

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        site = _site(target.careers_url) or _site(target.api_url) or target.slug
        if not site:
            raise ProviderError("adp-myjobs needs a myjobs.adp.com/<site>/... url")
        orgoid = str(target.options.get("orgoid") or "").strip()
        if not ORGOID_RE.match(orgoid):
            info = ctx.http.get_json(f"{API}/career-site/{quote(site)}", headers={"Accept": "application/json", "Accept-Language": "en-US"})
            orgoid = _s((info or {}).get("orgoid")) if isinstance(info, dict) else ""
            if not ORGOID_RE.match(orgoid):
                raise ProviderError(f'adp-myjobs: could not resolve orgoid for "{site}"; set options.orgoid')
        headers = {"Accept": "application/json", "Accept-Language": "en-US", "orgoid": orgoid}
        company = target.company or site
        jobs: list[Job] = []
        seen: set[str] = set()
        skip = 0
        for _ in range(MAX_PAGES):
            data = ctx.http.get_json(f"{API}/job-requisitions?rb=CareerSite&$top={PAGE_SIZE}&$skip={skip}", headers=headers)
            rows = data.get("jobRequisitions") if isinstance(data, dict) else None
            if not isinstance(rows, list):
                raise ProviderError("adp-myjobs: expected jobRequisitions[]")
            fresh = 0
            for r in rows:
                req = str(r.get("reqId") or "").strip()
                title = next((_s(r.get(k)) for k in ("jobTitle", "publishedJobTitle", "requisitionTitle") if _s(r.get(k))), "")
                if not req or not title or req in seen:
                    continue
                seen.add(req)
                fresh += 1
                jobs.append(self.job(title=title, url=f"https://{HOST}/{quote(site)}/cx/job-details?rb=CareerSite&reqId={quote(req)}",
                                     company=company, location=_location(r), source_id=req,
                                     extra={"requisition_id": str(r["clientRequisitionID"])} if r.get("clientRequisitionID") else {}).validate())
                if len(jobs) >= ctx.max_jobs:
                    return jobs
            skip += len(rows)
            total = data.get("count")
            if not rows or not fresh or (isinstance(total, int) and skip >= total) or (not isinstance(total, int) and len(rows) < PAGE_SIZE):
                break
        return jobs


PROVIDER = AdpMyJobs()
