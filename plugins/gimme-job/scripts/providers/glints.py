"""Glints (SEA) — public GraphQL searchJobsV3.

POST https://glints.com/api/v2-alc/graphql   (operationName searchJobsV3)
Mechanism from career-ops providers/glints.mjs (MIT); code is our own.
Target: query = keywords, options.country (ISO code, default ID).
"""
from __future__ import annotations

from ._base import Context, Job, Provider, ProviderError, Target
from ._parse import to_iso

API = "https://glints.com/api/v2-alc/graphql"
QUERY = """
query searchJobsV3($data: JobSearchConditionInput!) {
  searchJobsV3(data: $data) {
    jobsInPage { id title company { name brandName } city { name } country { code name }
      salaries { salaryType salaryMode maxAmount minAmount CurrencyCode } createdAt }
    expInfo hasMore
  }
}"""
HEADERS = {"Origin": "https://glints.com", "Referer": "https://glints.com/id/opportunities/jobs/explore"}


class Glints(Provider):
    name = "glints"
    wave = "W5"
    kind = "board"
    tenant = False
    hosts = ("glints.com",)

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        o = target.options
        country = (o.get("country") or "ID").upper()
        size = int(o.get("page_size") or 30)
        pages = int(o.get("max_pages") or 3)
        jobs: list[Job] = []
        for page in range(1, pages + 1):
            body = {"operationName": "searchJobsV3", "query": QUERY, "variables": {"data": {
                "SearchTerm": target.query or "", "CountryCode": country,
                "includeExternalJobs": True, "pageSize": size, "page": page}}}
            data = ctx.http.post_json(API, data=body, headers=HEADERS)
            block = ((data or {}).get("data") or {}).get("searchJobsV3")
            rows = (block or {}).get("jobsInPage")
            if not isinstance(rows, list):
                raise ProviderError("glints: unexpected GraphQL response")
            if not rows:
                break
            for it in rows:
                jid = str(it.get("id") or "").strip()
                title = str(it.get("title") or "").strip()
                if not jid or not title:
                    continue
                co = it.get("company") or {}
                sal = next((s for s in it.get("salaries") or [] if s.get("minAmount") or s.get("maxAmount")), None)
                kw = {}
                if sal:
                    kw = {"salary_min": sal.get("minAmount"), "salary_max": sal.get("maxAmount"),
                          "currency": sal.get("CurrencyCode") or "",
                          "salary_period": {"MONTHLY": "month", "YEARLY": "year", "HOURLY": "hour"}.get(
                              str(sal.get("salaryType") or "").upper(), "")}
                jobs.append(self.job(
                    title=title, url=f"https://glints.com/id/opportunities/jobs/{jid}",
                    company=str(co.get("name") or co.get("brandName") or "").strip(),
                    location=str((it.get("city") or {}).get("name") or "").strip(),
                    country=str((it.get("country") or {}).get("code") or "").strip(),
                    posted_at=to_iso(it.get("createdAt")), source_id=jid, **kw,
                ).validate())
                if len(jobs) >= ctx.max_jobs:
                    return jobs
            if block.get("hasMore") is False or len(rows) < size:
                break
        return jobs


PROVIDER = Glints()
