"""Welcome to the Jungle — Algolia index behind the site search, board-wide.

POST https://<appid>-dsn.algolia.net/1/indexes/wttj_jobs_production_en/query  {"params": "query=...&hitsPerPage=N"}
Credentials are NOT hardcoded: options.algolia_app / options.algolia_key or env
GIMME_JOB_WTTJ_ALGOLIA_APP / GIMME_JOB_WTTJ_ALGOLIA_KEY.
Mechanism from career-ops providers/wttj.mjs (MIT); code is our own.
"""
from __future__ import annotations

import os
import re
from urllib.parse import urlencode

from ._base import Context, Job, Provider, ProviderError, Target
from ._parse import to_iso

SITE = "https://www.welcometothejungle.com"
INDEX = "wttj_jobs_production_en"
ATTRS = ("name,slug,organization,offices,remote,published_at_timestamp,salary_yearly_minimum,"
         "salary_maximum,salary_period,salary_currency")
SLUG = re.compile(r"[a-z0-9_-]+", re.I)


def _pos(v) -> float:
    return float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) and v > 0 else 0.0


class Wttj(Provider):
    name = "wttj"
    wave = "W5"
    kind = "board"
    tenant = False
    hosts = ("www.welcometothejungle.com", "algolia.net")

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        o = target.options
        app = str(o.get("algolia_app") or os.environ.get("GIMME_JOB_WTTJ_ALGOLIA_APP") or "").strip()
        key = str(o.get("algolia_key") or os.environ.get("GIMME_JOB_WTTJ_ALGOLIA_KEY") or "").strip()
        if not app or not key:
            raise ProviderError("wttj needs GIMME_JOB_WTTJ_ALGOLIA_APP and GIMME_JOB_WTTJ_ALGOLIA_KEY "
                                "(or options.algolia_app / options.algolia_key)")
        if not re.fullmatch(r"[A-Za-z0-9]{6,16}", app):
            raise ProviderError("wttj: unexpected Algolia app id")
        queries = o.get("queries") or target.query
        if isinstance(queries, str):
            queries = queries.replace("\n", ",").split(",")
        queries = [str(q).strip() for q in queries or [] if str(q).strip()]
        filters = str(o.get("filters") or "").strip()
        if not queries and not filters:
            raise ProviderError("wttj is a global board: needs target.query / options.queries and/or options.filters")
        max_hits = min(int(o.get("max_hits") or 100), 1000 if filters else 200)
        url = f"https://{app.lower()}-dsn.algolia.net/1/indexes/{INDEX}/query"
        headers = {"x-algolia-application-id": app, "x-algolia-api-key": key, "Referer": SITE + "/"}
        jobs: dict[str, Job] = {}
        for q in queries or [""]:
            params = {"query": q, "hitsPerPage": max_hits, "attributesToRetrieve": ATTRS}
            if filters:
                params["filters"] = filters
            data = ctx.http.post_json(url, {"params": urlencode(params)}, headers=headers)
            if not isinstance(data, dict) or not isinstance(data.get("hits"), list):
                raise ProviderError(f"wttj: unexpected Algolia response for query {q!r}, expected {{hits: [...]}}")
            for h in data["hits"]:
                title = str(h.get("name") or "").strip()
                slug = str(h.get("slug") or "").strip()
                org = h.get("organization") or {}
                org_slug = str(org.get("slug") or "").strip()
                if not (title and slug and org_slug and SLUG.fullmatch(slug) and SLUG.fullmatch(org_slug)):
                    continue
                link = f"{SITE}/en/companies/{org_slug}/jobs/{slug}"
                if link in jobs:
                    continue
                offices = h.get("offices") or []
                office = offices[0] if offices else {}
                parts = [str(office.get(k)).strip() for k in ("city", "country") if office.get(k) and str(office[k]).strip()]
                remote = h.get("remote") == "fulltime"
                if remote:
                    parts.append("Remote")
                lo = _pos(h.get("salary_yearly_minimum"))
                hi = _pos(h.get("salary_maximum")) if h.get("salary_period") == "yearly" else 0.0
                ts = _pos(h.get("published_at_timestamp"))
                jobs[link] = self.job(
                    title=title, url=link, company=str(org.get("name") or "").strip() or "Welcome to the Jungle",
                    location=", ".join(parts), locations=parts, workplace="remote" if remote else "",
                    posted_at=to_iso(ts) if ts else "",
                    salary_min=(lo or hi) or None, salary_max=(hi or lo) or None,
                    currency=str(h.get("salary_currency") or "").strip().upper() if (lo or hi) else "",
                    salary_period="year" if (lo or hi) else "", source_id=str(h.get("objectID") or slug),
                ).validate()
                if len(jobs) >= ctx.max_jobs:
                    return list(jobs.values())
        return list(jobs.values())


PROVIDER = Wttj()
