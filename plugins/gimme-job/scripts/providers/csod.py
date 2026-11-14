"""Cornerstone OnDemand (csod) career sites — anonymous token from the home page, then POST career-site/v1/search.

Mechanism from career-ops providers/csod.mjs (MIT).
"""
from __future__ import annotations

import html
import re
from datetime import datetime
from urllib.parse import parse_qs, quote, urlsplit

from ._base import Context, Job, Provider, ProviderError, Target

PAGE_SIZE = 25
MAX_PAGES = 40


def _cfg(url: str):
    u = urlsplit(url or "")
    host = u.netloc.lower()
    if u.scheme != "https" or not (host == "csod.com" or host.endswith(".csod.com")):
        return None
    m = re.search(r"/ux/ats/careersite/(\d+)(?:/|$)", u.path, re.I)
    if not m:
        return None
    corp = (parse_qs(u.query).get("c") or [host.split(".")[0]])[0]
    return {"origin": f"https://{u.netloc}", "site": int(m.group(1)), "corp": corp}


def _date(raw) -> str:
    try:
        return datetime.strptime(str(raw or "").strip(), "%m/%d/%Y").date().isoformat()
    except ValueError:
        return ""


def _locations(raw) -> list[str]:
    out: list[str] = []
    for l in raw or []:
        if not isinstance(l, dict):
            continue
        city, country = str(l.get("city") or "").strip(), str(l.get("country") or "").strip()
        s = (f"{city}, {country}" if country else city) if city else country
        if s and s not in out:
            out.append(s)
    return out


class Csod(Provider):
    name = "csod"
    wave = "W2"
    kind = "ats"
    tenant = True
    hosts = ("csod.com",)

    def detect(self, careers_url: str):
        c = _cfg(careers_url)
        if not c:
            return None
        return Target(slug=c["corp"], careers_url=careers_url, api_url=f"{c['origin']}/services/x/career-site/v1/search")

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        c = _cfg(target.careers_url) or _cfg(target.api_url)
        if not c:
            raise ProviderError("csod needs an https *.csod.com/ux/ats/careersite/<id>/ url")
        home = f"{c['origin']}/ux/ats/careersite/{c['site']}/home?c={quote(c['corp'])}"
        r = ctx.http.get(home, headers={"Accept": "text/html"})
        m = re.search(r'"token"\s*:\s*"([A-Za-z0-9._-]+)"', r.text)
        if not m:
            raise ProviderError(f"csod: no anonymous token on {home}")
        headers = {"Authorization": f"Bearer {m.group(1)}"}
        pair = (r.headers.get("set-cookie") or "").split(";", 1)[0].strip()
        if "=" in pair:
            headers["Cookie"] = pair
        company = target.company or c["corp"]
        jobs: list[Job] = []
        seen: set[str] = set()
        for page in range(1, MAX_PAGES + 1):
            body = {"careerSiteId": c["site"], "careerSitePageId": c["site"], "pageNumber": page, "pageSize": PAGE_SIZE,
                    "cultureId": 1, "cultureName": "en-US", "searchText": "", "states": [], "countryCodes": [], "cities": [],
                    "placeID": "", "radius": None, "postingsWithinDays": None, "customFieldCheckboxKeys": [],
                    "customFieldDropdowns": [], "customFieldRadios": []}
            data = ctx.http.post_json(f"{c['origin']}/services/x/career-site/v1/search", body, headers=headers)
            d = (data or {}).get("data") or {}
            reqs = d.get("requisitions") or []
            fresh = 0
            for q in reqs:
                rid = str(q.get("requisitionId") or "")
                title = " ".join(html.unescape(re.sub(r"<[^>]*>", " ", str(q.get("displayJobTitle") or ""))).split())
                if not rid or not title or rid in seen:
                    continue
                seen.add(rid)
                fresh += 1
                locs = _locations(q.get("locations"))
                jobs.append(self.job(title=title, url=f"{c['origin']}/ux/ats/careersite/{c['site']}/home/requisition/{rid}?c={quote(c['corp'])}",
                                     company=company, locations=locs, location=" / ".join(locs),
                                     posted_at=_date(q.get("postingEffectiveDate")), source_id=rid).validate())
                if len(jobs) >= ctx.max_jobs:
                    return jobs
            total = d.get("totalCount")
            if not fresh or len(reqs) < PAGE_SIZE or (isinstance(total, int) and page * PAGE_SIZE >= total):
                break
        return jobs


PROVIDER = Csod()
