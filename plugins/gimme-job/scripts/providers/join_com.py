"""JOIN (join.com) — company id from the careers page __NEXT_DATA__, then the candidate GraphQL API.

Mechanism from career-ops providers/join.mjs (MIT); code is our own. PROVIDER.name is "join".
"""
from __future__ import annotations

from urllib.parse import urlsplit

from ._base import Context, Job, Provider, ProviderError, Target
from ._parse import html_to_text, next_data, to_iso

GRAPHQL = "https://join.com/candidate-api/graphql"
PAGE_SIZE = 100
MAX_PAGES = 50
QUERY = """query PublicJobsList($input: PublicJobsQueryInput!) {
  publicJobs(input: $input) {
    items { id title createdAt descriptionHtml language { iso6391 } workplaceType remoteType
            remoteRegion { name } city { cityName countryName } country { name } }
    pageInfo { pageCount }
  }
}"""


def _slug(url: str) -> str:
    p = urlsplit((url or "").strip())
    if p.scheme != "https" or (p.hostname or "").lower() != "join.com":
        return ""
    parts = [x for x in p.path.split("/") if x]
    return parts[1] if len(parts) >= 2 and parts[0] == "companies" else ""


def _location(j: dict) -> str:
    city = ((j.get("city") or {}).get("cityName") or "").strip()
    country = ""
    for v in ((j.get("country") or {}).get("name"), (j.get("city") or {}).get("countryName")):
        if isinstance(v, str) and v.strip():
            country = v.strip()
            break
    wt = j.get("workplaceType")
    if wt == "REMOTE":
        region = ((j.get("remoteRegion") or {}).get("name") or "").strip()
        rt = j.get("remoteType")
        area = "worldwide" if rt == "ANYWHERE" else region if rt == "REGION" else country
        return f"Remote ({area})" if area else "Remote"
    place = ", ".join(x for x in (city, country) if x)
    if wt == "HYBRID":
        return f"{place} (hybrid)" if place else "Hybrid"
    return place


class Join(Provider):
    name = "join"
    wave = "W4"
    kind = "ats"
    tenant = True
    hosts = ("join.com",)

    def detect(self, careers_url: str):
        s = _slug(careers_url)
        return Target(slug=s, careers_url=careers_url) if s else None

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        slug = target.slug or _slug(target.careers_url)
        if not slug:
            raise ProviderError("join needs https://join.com/companies/<slug>")
        cid = target.options.get("company_id") if target.options else None
        if not isinstance(cid, int):
            html = ctx.http.get_text(f"https://join.com/companies/{slug}")
            pp = ((next_data(html) or {}).get("props") or {}).get("pageProps") or {}
            company = ((pp.get("pageData") or pp.get("initialState") or {}).get("company")) or {}
            cid = company.get("id")
            if not isinstance(cid, int):
                raise ProviderError("join: __NEXT_DATA__ not found or has no company id")
        jobs: list[Job] = []
        pages, page = 1, 1
        while page <= min(pages, MAX_PAGES):
            data = ctx.http.post_json(GRAPHQL, {
                "operationName": "PublicJobsList", "query": QUERY,
                "variables": {"input": {"companyId": cid, "paginationPage": {"page": page, "pageSize": PAGE_SIZE},
                                        "filters": {}}},
            })
            errs = (data or {}).get("errors")
            if errs:
                raise ProviderError(f"join: publicJobs failed: {(errs[0] or {}).get('message', 'unknown')}")
            pj = ((data or {}).get("data") or {}).get("publicJobs") or {}
            items = pj.get("items")
            if not isinstance(items, list):
                raise ProviderError("join: publicJobs response has no items array")
            pages = (pj.get("pageInfo") or {}).get("pageCount") or 0
            for j in items:
                if not isinstance(j, dict) or not isinstance(j.get("id"), int) or not (j.get("title") or "").strip():
                    continue
                jobs.append(self.job(
                    title=j["title"], url=f"https://join.com/companies/{slug}/{j['id']}",
                    company=target.company or slug, location=_location(j),
                    workplace={"REMOTE": "remote", "HYBRID": "hybrid", "ONSITE": "onsite"}.get(j.get("workplaceType"), ""),
                    posted_at=to_iso(j.get("createdAt")), description=html_to_text(j.get("descriptionHtml") or ""),
                    source_id=str(j["id"]),
                ).validate())
                if len(jobs) >= ctx.max_jobs:
                    return jobs
            page += 1
        return jobs


PROVIDER = Join()
