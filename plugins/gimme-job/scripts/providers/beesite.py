"""BeeSite (Milch & Zucker) — GET https://<host>.beesite.de/search?data=<json>.

Mechanism from career-ops providers/beesite.mjs (MIT); code is our own.
Target.options may carry languageCode (default EN) and searchCriteria (list).
"""
from __future__ import annotations

import html as htmllib
import json
import re
from urllib.parse import quote, urlsplit

from ._base import Context, Job, Provider, ProviderError, Target
from ._parse import to_iso

PAGE_SIZE = 100
MAX_PAGES = 40
MAX_JOBS = 1000
DESCRIPTOR = ["PositionID", "PositionTitle", "PositionURI", "PositionLocation.CityName", "PublicationStartDate"]


def _origin(url: str) -> str:
    p = urlsplit((url or "").strip())
    host = (p.netloc or "").lower()
    if p.scheme not in ("http", "https") or not (host == "beesite.de" or host.endswith(".beesite.de")):
        return ""
    return f"{p.scheme}://{p.netloc}"


class BeeSite(Provider):
    name = "beesite"
    wave = "W4"
    kind = "ats"
    tenant = True
    hosts = ("beesite.de",)

    def detect(self, careers_url: str):
        o = _origin(careers_url)
        if not o:
            return None
        return Target(slug=urlsplit(o).hostname.split(".")[0], careers_url=careers_url, api_url=o + "/search")

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        o = _origin(target.api_url) or _origin(target.careers_url)
        if not o:
            raise ProviderError("beesite needs a *.beesite.de url")
        opts = target.options or {}
        lang = opts.get("languageCode") if isinstance(opts.get("languageCode"), str) else "EN"
        crit = opts.get("searchCriteria") if isinstance(opts.get("searchCriteria"), list) else []
        company = target.company or urlsplit(o).hostname.split(".")[0]
        jobs: list[Job] = []
        seen: set[str] = set()
        total = None
        for page in range(MAX_PAGES):
            data = {"LanguageCode": lang, "SearchParameters": {
                "FirstItem": page * PAGE_SIZE + 1, "CountItem": PAGE_SIZE,
                "Sort": [{"Criterion": "PublicationStartDate", "Direction": "DESC"}],
                "MatchedObjectDescriptor": DESCRIPTOR}, "SearchCriteria": crit}
            res = ctx.http.get_json(f"{o}/search?data={quote(json.dumps(data, separators=(',', ':')), safe='')}")
            sr = (res or {}).get("SearchResult") if isinstance(res, dict) else None
            if not isinstance(sr, dict):
                raise ProviderError("beesite: unexpected response, missing SearchResult")
            if total is None and isinstance(sr.get("SearchResultCountAll"), int):
                total = sr["SearchResultCountAll"]
            items = sr.get("SearchResultItems") if isinstance(sr.get("SearchResultItems"), list) else []
            if not items:
                break
            fresh = 0
            for item in items:
                d = (item or {}).get("MatchedObjectDescriptor")
                if not isinstance(d, dict):
                    continue
                jid = str(item.get("MatchedObjectId") if item.get("MatchedObjectId") is not None else d.get("PositionID") or "")
                title = re.sub(r"\s+", " ", htmllib.unescape(re.sub(r"<[^>]*>", " ", str(d.get("PositionTitle") or "")))).strip()
                url = str(d.get("PositionURI") or "").strip()
                if not jid or not title or not re.match(r"https?://", url, re.I) or jid in seen:
                    continue
                seen.add(jid)
                fresh += 1
                locs = d.get("PositionLocation") if isinstance(d.get("PositionLocation"), list) else []
                cities: list[str] = []
                for l in locs:
                    c = str((l or {}).get("CityName") or "").strip()
                    if c and c not in cities:
                        cities.append(c)
                jobs.append(self.job(title=title, url=url, company=company, location=" / ".join(cities),
                                     posted_at=to_iso(d.get("PublicationStartDate")), source_id=jid).validate())
                if len(jobs) >= min(MAX_JOBS, ctx.max_jobs):
                    return jobs
            if fresh == 0 or (total is not None and (page + 1) * PAGE_SIZE >= total):
                break
        return jobs


PROVIDER = BeeSite()
