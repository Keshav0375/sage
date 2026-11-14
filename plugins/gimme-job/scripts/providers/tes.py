"""Tes Jobs (UK education) — public tRPC search endpoint, board-wide.

GET https://www.tes.com/jobs/api/trpc/jobs.search?batch=1&input=<json>
Mechanism from career-ops providers/tes.mjs (MIT); code is our own.
"""
from __future__ import annotations

import html
import json
import re
from urllib.parse import urlencode

from ._base import Context, Job, Provider, ProviderError, Target
from ._parse import to_iso

ORIGIN = "https://www.tes.com"
SEARCH = ORIGIN + "/jobs/api/trpc/jobs.search"
PAGE_SIZE = 50
VACANCY = re.compile(r"/jobs/vacancy/[a-z0-9][a-z0-9-]*-\d+")
_AMT = r"(£|€|HK\$|[A-Z]{3}\s*)([\d,]+(?:\.\d+)?)"
SALARY = re.compile(rf"^{_AMT}(?:\s*-\s*{_AMT})?\s+per\s+(?:year|annum)$", re.I)
SIGNS = {"£": "GBP", "€": "EUR", "HK$": "HKD"}


def _text(v) -> str:
    return " ".join(html.unescape(v).split()) if isinstance(v, str) else ""


def _cur(sign: str) -> str:
    s = sign.strip()
    return SIGNS.get(s) or s.upper()


def parse_salary_range(rng) -> dict:
    m = SALARY.match(_text(rng))
    if not m:
        return {}
    cur = _cur(m.group(1))
    if m.group(3) and _cur(m.group(3)) != cur:
        return {}
    lo = float(m.group(2).replace(",", ""))
    hi = float(m.group(4).replace(",", "")) if m.group(4) else lo
    if lo <= 0 or hi < lo:
        return {}
    return {"salary_min": lo, "salary_max": hi, "currency": cur, "salary_period": "year"}


def search_url(keywords: str, page: int) -> str:
    inp = {"0": {"json": {"limit": PAGE_SIZE, "filters": {
        "keywords": keywords, "locations": [], "excludedLocations": [],
        "filters": {"contractTerms": [], "contractTypes": [], "subjects": [], "workplaces": [], "positions": [],
                    "location": {"distance": 30, "distanceUnit": "mi"}},
        "sort": "date", "page": page}, "siteCountry": "gb"}}}
    return f"{SEARCH}?{urlencode({'batch': '1', 'input': json.dumps(inp, separators=(',', ':'))})}"


def payload(body) -> dict:
    first = body[0] if isinstance(body, list) and body else None
    if isinstance(first, dict) and first.get("error"):
        raise ProviderError("tes: search endpoint returned an error: " + _text(((first["error"] or {}).get("json") or {}).get("message")))
    data = (((first or {}).get("result") or {}).get("data") or {}).get("json") if isinstance(first, dict) else None
    if not isinstance(data, dict) or not isinstance(data.get("jobs"), list):
        raise ProviderError("tes: unexpected search response")
    return data


class Tes(Provider):
    name = "tes"
    wave = "W5"
    kind = "board"
    tenant = False
    hosts = ("www.tes.com",)

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        kw = (target.query or target.options.get("keywords") or "").strip()
        if len(kw) > 100 or any(ord(c) < 32 for c in kw):
            raise ProviderError("tes: keywords must be one line of at most 100 characters")
        max_pages = min(int(target.options.get("max_pages") or 150), 400)
        jobs: dict[str, Job] = {}
        for page in range(1, max_pages + 1):
            data = payload(ctx.http.get_json(search_url(kw, page)))
            for r in data["jobs"]:
                canon = r.get("canonicalUrl") if isinstance(r, dict) else None
                title = _text(r.get("title")) if isinstance(r, dict) else ""
                if not title or not isinstance(canon, str) or not VACANCY.fullmatch(canon):
                    continue
                url = ORIGIN + canon
                rid = r.get("id")
                key = str(rid) if isinstance(rid, int) and rid > 0 else url
                if key in jobs:
                    continue
                loc = _text(r.get("displayLocation"))
                jobs[key] = self.job(
                    title=title, url=url, company=_text((r.get("employer") or {}).get("name")) or "Tes",
                    location=loc, locations=[loc] if loc else [],
                    posted_at=to_iso((r.get("advert") or {}).get("startDate")),
                    closes_at=to_iso((r.get("application") or {}).get("closeDate")),
                    description=_text(r.get("shortDescription")),
                    source_id=str(rid) if key != url else "",
                    **parse_salary_range((r.get("salary") or {}).get("range")),
                ).validate()
                if len(jobs) >= ctx.max_jobs:
                    return list(jobs.values())
            total = data.get("totalPages")
            if len(data["jobs"]) < PAGE_SIZE or (isinstance(total, int) and 0 < total <= page):
                break
        return list(jobs.values())


PROVIDER = Tes()
