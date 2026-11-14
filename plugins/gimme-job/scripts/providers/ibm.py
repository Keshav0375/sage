"""IBM Careers — public Elasticsearch-style search API (no auth).

POST https://www-api.ibm.com/search/api/v2 {appId:"careers", post_filter, size:30, from:N, ...}
-> hits.hits[]._source {title, url, dcdate, field_keyword_19 (location), field_keyword_17 (work mode)}
Filters: options['ibm'] = {country, categories[]}.
Mechanism from career-ops providers/ibm.mjs (MIT); code is our own.
"""
from __future__ import annotations

from urllib.parse import urlsplit

from ._base import Context, Job, Provider, ProviderError, Target
from ._parse import to_iso, workplace_from

API = "https://www-api.ibm.com/search/api/v2"
PAGE_SIZE = 30


def build_post_filter(cfg: dict) -> dict:
    must = []
    cats = [c.strip() for c in (cfg.get("categories") or []) if isinstance(c, str) and c.strip()]
    if cats:
        must.append({"bool": {"should": [{"term": {"field_keyword_08": c}} for c in cats]}})
    country = (cfg.get("country") or "").strip() if isinstance(cfg.get("country"), str) else ""
    if country:
        must.append({"term": {"field_keyword_05": country}})
    return {"bool": {"must": must}}


class Ibm(Provider):
    name = "ibm"
    wave = "W3"
    kind = "company"
    tenant = False
    hosts = ("ibm.com",)

    def detect(self, careers_url: str):
        h = urlsplit(careers_url or "").netloc.lower()
        if h in ("www.ibm.com", "ibm.com") and "/careers" in (careers_url or ""):
            return Target(company="IBM", careers_url=careers_url)
        return None

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        cfg = target.options.get("ibm") if isinstance(target.options.get("ibm"), dict) else {}
        post_filter = build_post_filter(cfg)
        max_pages = min(int(target.options.get("max_pages") or 20), 300)
        jobs: list[Job] = []
        for page in range(max_pages):
            body = {
                "appId": "careers", "scopes": ["careers2"],
                "query": {"bool": {"must": ([{"match": {"title": target.query}}] if target.query else [])}},
                "post_filter": post_filter, "size": PAGE_SIZE, "from": page * PAGE_SIZE,
                "sort": [{"_score": "desc"}, {"pageviews": "desc"}], "lang": "zz", "localeSelector": {},
                "sm": {"query": target.query or "", "lang": "zz"},
                "_source": ["_id", "title", "url", "description", "language", "dcdate", "field_keyword_05",
                            "field_keyword_08", "field_keyword_17", "field_keyword_18", "field_keyword_19"],
            }
            data = ctx.http.post_json(API, data=body)
            hits = ((data or {}).get("hits") or {}).get("hits") if isinstance(data, dict) else None
            if not isinstance(hits, list):
                raise ProviderError("ibm: expected hits.hits[]")
            for h in hits:
                s = (h or {}).get("_source") or {}
                title = (s.get("title") or "").strip() if isinstance(s.get("title"), str) else ""
                url = (s.get("url") or "").strip() if isinstance(s.get("url"), str) else ""
                if not title or not url.lower().startswith(("http://", "https://")):
                    continue
                loc = (s.get("field_keyword_19") or "").strip() if isinstance(s.get("field_keyword_19"), str) else ""
                mode = (s.get("field_keyword_17") or "").strip() if isinstance(s.get("field_keyword_17"), str) else ""
                jobs.append(self.job(
                    title=title, url=url, company="IBM",
                    location=" · ".join(x for x in (loc, mode) if x),
                    workplace=workplace_from(mode), posted_at=to_iso(s.get("dcdate")),
                    country=(s.get("field_keyword_05") or "") if isinstance(s.get("field_keyword_05"), str) else "",
                    department=(s.get("field_keyword_08") or "") if isinstance(s.get("field_keyword_08"), str) else "",
                    source_id=str((h or {}).get("_id") or ""),
                ).validate())
                if len(jobs) >= ctx.max_jobs:
                    return jobs
            if len(hits) < PAGE_SIZE:
                break
        return jobs


PROVIDER = Ibm()
