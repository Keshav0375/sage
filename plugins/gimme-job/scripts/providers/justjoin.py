"""Just Join IT (PL) — public candidate API, cursor paginated.

GET https://justjoin.it/api/candidate-api/offers?from=<cursor>&itemsCount=100&...
Mechanism from career-ops providers/justjoin.mjs (MIT); code is our own.
"""
from __future__ import annotations

from urllib.parse import urlencode

from ._base import Context, Job, Provider, ProviderError, Target
from ._parse import to_iso, workplace_from

API = "https://justjoin.it/api/candidate-api/offers"
JOB = "https://justjoin.it/job-offer/"


class JustJoin(Provider):
    name = "justjoin"
    wave = "W5"
    kind = "board"
    tenant = False
    hosts = ("justjoin.it",)

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        o = target.options
        size = int(o.get("page_size") or 100)
        pages = min(int(o.get("max_pages") or 5), 50)
        kw = (target.query or "").lower().split()
        jobs: list[Job] = []
        cursor = 0
        for _ in range(pages):
            q = {"from": cursor, "itemsCount": size, "cityRadius": int(o.get("city_radius") or 30),
                 "currency": str(o.get("currency") or "pln").lower(), "orderBy": "descending",
                 "sortBy": "publishedAt", "keywordType": "any", "isPromoted": "true"}
            data = ctx.http.get_json(f"{API}?{urlencode(q)}")
            if not isinstance(data, dict) or not isinstance(data.get("data"), list):
                raise ProviderError("justjoin: unexpected response, expected {data: [...]}")
            rows = data["data"]
            for r in rows:
                slug = str(r.get("slug") or "").strip()
                title = str(r.get("title") or "").strip()
                if not slug or not title:
                    continue
                if kw and not all(w in title.lower() for w in kw):
                    continue
                cities = [str(l.get("city") or "").strip() for l in r.get("locations") or [] if l.get("city")]
                if not cities and r.get("city"):
                    cities = [str(r["city"]).strip()]
                jobs.append(self.job(
                    title=title, url=JOB + slug, company=str(r.get("companyName") or "").strip(),
                    location=", ".join(dict.fromkeys(cities)), locations=cities, country="PL",
                    workplace=workplace_from(r.get("workplaceType")),
                    posted_at=to_iso(r.get("lastPublishedAt") or r.get("publishedAt")),
                    source_id=str(r.get("guid") or slug),
                ).validate())
                if len(jobs) >= ctx.max_jobs:
                    return jobs
            nxt = ((data.get("meta") or {}).get("next") or {}).get("cursor")
            if nxt is None or not rows:
                break
            try:
                cursor = int(nxt)
            except (TypeError, ValueError):
                break
        return jobs


PROVIDER = JustJoin()
