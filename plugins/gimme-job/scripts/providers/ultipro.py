"""UKG Pro / UltiPro Recruiting — POST .../JobBoardView/LoadSearchResults (public job board).

Mechanism from career-ops providers/ultipro.mjs (MIT); list path only.
"""
from __future__ import annotations

import re
from urllib.parse import quote, urlsplit

from ._base import Context, Job, Provider, ProviderError, Target
from ._parse import html_to_text, to_iso

HOST_RE = re.compile(r"^recruiting\d*\.ultipro\.(?:com|ca)$", re.I)
PATH_RE = re.compile(r"^/([^/]+)/JobBoard/([^/]+)(?:/|$)")
PAGE_SIZE = 50
MAX_PAGES = 100


def _tenant(url: str):
    p = urlsplit(url or "")
    if p.scheme != "https" or not HOST_RE.match(p.netloc.lower()):
        return None
    m = PATH_RE.match(p.path)
    return {"origin": f"https://{p.netloc.lower()}", "tenant": m.group(1), "board": m.group(2)} if m else None


def _locations(locs) -> list[str]:
    out: list[str] = []
    for l in locs or []:
        if isinstance(l, str):
            label = l.strip()
        elif isinstance(l, dict):
            addr = l.get("Address") or {}
            st = (addr.get("State") or {}).get("Code") if isinstance(addr.get("State"), dict) else ""
            label = ", ".join(x for x in (str(addr.get("City") or "").strip(), str(st or "").strip()) if x) or str(l.get("LocalizedName") or "").strip()
        else:
            continue
        if label and label not in out:
            out.append(label)
    return out


class UltiPro(Provider):
    name = "ultipro"
    wave = "W2"
    kind = "ats"
    tenant = True
    hosts = ("ultipro.com", "ultipro.ca")

    def detect(self, careers_url: str):
        t = _tenant(careers_url)
        if not t:
            return None
        return Target(slug=t["tenant"], careers_url=careers_url,
                      api_url=f"{t['origin']}/{t['tenant']}/JobBoard/{t['board']}/JobBoardView/LoadSearchResults")

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        t = _tenant(target.api_url) or _tenant(target.careers_url)
        if not t:
            raise ProviderError("ultipro needs an https recruiting*.ultipro.com/<tenant>/JobBoard/<id> url")
        api = f"{t['origin']}/{t['tenant']}/JobBoard/{t['board']}/JobBoardView/LoadSearchResults"
        company = target.company or t["tenant"]
        jobs: list[Job] = []
        seen: set[str] = set()
        skip = 0
        for _ in range(MAX_PAGES):
            body = {"opportunitySearch": {"Top": PAGE_SIZE, "Skip": skip, "QueryString": "",
                                          "OrderBy": [{"Value": "postedDateDesc", "PropertyName": "PostedDate", "Ascending": False}],
                                          "Filters": []},
                    "matchCriteria": {"PreferredJobs": [], "Educations": [], "LicenseAndCertifications": [],
                                      "Skills": [], "hasNoLicenses": False, "SkippedSkills": []}}
            data = ctx.http.post_json(api, body)
            raw = (data or {}).get("opportunities") if isinstance(data, dict) else None
            if not isinstance(raw, list):
                raise ProviderError("ultipro: unrecognized LoadSearchResults response")
            if not raw:
                break
            fresh = 0
            for it in raw:
                jid = str(it.get("Id") or "").strip()
                title = str(it.get("Title") or "").strip()
                if not jid or not title or jid in seen:
                    continue
                seen.add(jid)
                fresh += 1
                locs = _locations(it.get("Locations"))
                jobs.append(self.job(
                    title=title, url=f"{t['origin']}/{t['tenant']}/JobBoard/{t['board']}/OpportunityDetail?opportunityId={quote(jid, safe='')}",
                    company=company, locations=locs, location=" / ".join(locs), posted_at=to_iso(it.get("PostedDate")),
                    description=html_to_text(it.get("BriefDescription") or ""), source_id=jid).validate())
                if len(jobs) >= ctx.max_jobs:
                    return jobs
            if not fresh or len(raw) < PAGE_SIZE:
                break
            skip += len(raw)
        return jobs


PROVIDER = UltiPro()
