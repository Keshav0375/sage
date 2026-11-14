"""Oracle Cloud HCM Candidate Experience — public recruitingCEJobRequisitions REST finder.

Mechanism from career-ops providers/oraclecloud.mjs (MIT).
"""
from __future__ import annotations

import html
import re
from urllib.parse import quote, urlsplit

from ._base import Context, Job, Provider, ProviderError, Target
from ._parse import to_iso, workplace_from

HOST_RE = re.compile(r"^[a-z0-9-]+\.fa\.(?:[a-z0-9-]+\.)?(?:ocs\.)?oraclecloud(?:[1-9][0-9]?)?\.com$", re.I)
PAGE_SIZE = 200
MAX_PAGES = 25
FACETS = "LOCATIONS%3BWORK_LOCATIONS%3BWORKPLACE_TYPES%3BTITLES%3BCATEGORIES%3BORGANIZATIONS%3BPOSTING_DATES%3BFLEX_FIELDS"


def _site(target: Target):
    for raw in (target.api_url, target.careers_url):
        p = urlsplit(raw or "")
        if p.scheme != "https" or not HOST_RE.match(p.netloc.lower()):
            continue
        segs = [s for s in p.path.split("/") if s]
        lang = segs[segs.index("CandidateExperience") + 1] if "CandidateExperience" in segs and segs.index("CandidateExperience") + 1 < len(segs) else "en"
        site = segs[segs.index("sites") + 1] if "sites" in segs and segs.index("sites") + 1 < len(segs) else "CX_1"
        site = target.options.get("siteNumber") or site
        return {"host": p.netloc.lower(), "lang": lang, "site": site, "location_id": target.options.get("locationId")}
    return None


def _api(site, offset: int) -> str:
    finder = f"findReqs;siteNumber={site['site']},facetsList={FACETS},limit={PAGE_SIZE},sortBy=POSTING_DATES_DESC,offset={offset}"
    if site["location_id"]:
        finder += f",locationId={site['location_id']}"
    return (f"https://{site['host']}/hcmRestApi/resources/latest/recruitingCEJobRequisitions?onlyData=true"
            f"&expand={quote('requisitionList.workLocation,requisitionList.secondaryLocations')}"
            f"&finder={finder}&limit={PAGE_SIZE}&offset={offset}")


class OracleCloud(Provider):
    name = "oraclecloud"
    wave = "W2"
    kind = "ats"
    tenant = True
    hosts = ("oraclecloud.com",)

    def detect(self, careers_url: str):
        t = Target(careers_url=careers_url)
        s = _site(t)
        if not s:
            return None
        return Target(slug=s["site"], careers_url=careers_url, api_url=_api(s, 0))

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        s = _site(target) or _site(Target(careers_url=target.api_url))
        if not s:
            raise ProviderError("oraclecloud needs an https *.fa.*.oraclecloud.com url")
        jobs: list[Job] = []
        for page in range(MAX_PAGES):
            offset = page * PAGE_SIZE
            data = ctx.http.get_json(_api(s, offset))
            item = ((data or {}).get("items") or [None])[0] or {}
            reqs = item.get("requisitionList") or []
            for r in reqs:
                rid = str(r.get("Id") or r.get("RequisitionNumber") or "")
                url = (r.get("ExternalURL") or "").strip() or (
                    f"https://{s['host']}/hcmUI/CandidateExperience/{s['lang']}/sites/{s['site']}/job/{rid}" if rid else "")
                loc = (r.get("PrimaryLocation") or "").strip()
                if not loc and r.get("workLocation"):
                    w = r["workLocation"][0] or {}
                    loc = ", ".join(x for x in (w.get("TownOrCity"), w.get("Region"), w.get("Country")) if x)
                wt = r.get("WorkplaceTypeCode")
                jobs.append(self.job(
                    title=r.get("Title") or "", url=url, company=target.company or s["host"].split(".")[0],
                    location=loc,
                    workplace={"ORA_REMOTE": "remote", "ORA_HYBRID": "hybrid", "ORA_ONSITE": "onsite"}.get(wt, ""),
                    description=html.unescape(r.get("ShortDescriptionStr") or ""),
                    posted_at=to_iso(r.get("PostedDate")), department=r.get("JobFamily") or "",
                    source_id=rid).validate())
                if len(jobs) >= ctx.max_jobs:
                    return jobs
            total = item.get("TotalJobsCount")
            if not reqs or (isinstance(total, int) and offset + PAGE_SIZE >= total) or (total is None and len(reqs) < PAGE_SIZE):
                break
        return jobs


PROVIDER = OracleCloud()
