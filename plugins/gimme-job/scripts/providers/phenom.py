"""Phenom People career sites — POST /widgets with ddoKey=refineSearch.

Mechanism from career-ops providers/phenom.mjs (MIT). Not URL-detectable (branded domains); pass careers_url.
Optional target.options: urlPrefix, lang, country, selectedFields.
"""
from __future__ import annotations

import html
import re
import unicodedata
from urllib.parse import quote, urlsplit

from ._base import Context, Job, Provider, ProviderError, Target
from ._parse import to_iso

PAGE_SIZE = 100
MAX_PAGES = 20


def slugify(title: str) -> str:
    s = unicodedata.normalize("NFKD", title)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-zA-Z0-9]+", "-", s).strip("-") or "job"


def _txt(v) -> str:
    return " ".join(html.unescape(re.sub(r"<[^>]*>", " ", str(v or ""))).split())


class Phenom(Provider):
    name = "phenom"
    wave = "W2"
    kind = "ats"
    tenant = True
    hosts = ("phenompeople.com",)

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        raw = target.api_url or target.careers_url
        p = urlsplit(raw or "")
        if p.scheme not in ("http", "https") or not p.netloc:
            raise ProviderError("phenom needs a careers_url")
        origin = f"{p.scheme}://{p.netloc}"
        o = target.options
        prefix = str(o.get("urlPrefix") or "global/en").strip("/")
        country = o.get("country") or "global"
        jobs: list[Job] = []
        seen: set[str] = set()
        for page in range(MAX_PAGES):
            body = {"lang": o.get("lang") or "en_global", "deviceType": "desktop", "country": country,
                    "pageName": "search-results", "ddoKey": "refineSearch", "sortBy": "", "subsearch": "",
                    "from": page * PAGE_SIZE, "jobs": True, "counts": True, "all_fields": ["category", "country", "city"],
                    "size": PAGE_SIZE, "clearAll": False, "jdsource": "facets", "isSliderEnable": False,
                    "pageId": "page10", "siteType": "external", "keywords": "", "global": country == "global",
                    "selected_fields": o.get("selectedFields") or {}, "locationData": {}}
            data = ctx.http.post_json(f"{origin}/widgets", body)
            rs = (data or {}).get("refineSearch") or {}
            rows = (rs.get("data") or {}).get("jobs") or []
            fresh = 0
            for r in rows:
                jid = str(r.get("jobId") or "")
                title = _txt(r.get("title"))
                if not jid or not title or jid in seen:
                    continue
                seen.add(jid)
                fresh += 1
                loc = _txt(r.get("location") or r.get("cityStateCountry") or r.get("cityState"))
                if not loc:
                    loc = ", ".join(dict.fromkeys(str(r.get(k)).strip() for k in ("city", "state", "country") if r.get(k)))
                jobs.append(self.job(
                    title=title, url=f"{origin}/{prefix}/job/{quote(jid, safe='')}/{slugify(title)}",
                    company=target.company or p.netloc.split(".")[-2 if p.netloc.count(".") else 0],
                    location=loc, posted_at=to_iso(r.get("postedDate") or r.get("dateCreated")),
                    department=_txt(r.get("category")), source_id=jid).validate())
                if len(jobs) >= ctx.max_jobs:
                    return jobs
            total = rs.get("totalHits")
            if not fresh or (isinstance(total, int) and (page + 1) * PAGE_SIZE >= total):
                break
        return jobs


PROVIDER = Phenom()
