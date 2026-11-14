"""RedRover K-12 — GraphQL at https://api.redroverk12.com/graphql for jobs.redroverk12.com/org/<id>.

Mechanism from career-ops providers/redrover.mjs (MIT); code is our own.
"""
from __future__ import annotations

import re
from urllib.parse import urlsplit

from ._base import Context, Job, Provider, ProviderError, Target
from ._parse import to_iso

API = "https://api.redroverk12.com/graphql"
HOST = "jobs.redroverk12.com"
QUERY = """query GetJobPostings($search: JobPostingSearchInput!) {
  jobSeekerSiteUnauthenticated {
    jobPostingSearch(search: $search) {
      results { id name organizationName location { name } activePublicOnDateUtc closedOnDateUtc allowsRemote }
      hasMoreData
    }
  }
}"""


def _org(url: str) -> str:
    p = urlsplit((url or "").strip())
    if p.scheme != "https" or p.netloc.lower() != HOST:
        return ""
    m = re.match(r"^/org/(\d+)(?:/|$)", p.path)
    return m.group(1) if m else ""


class RedRover(Provider):
    name = "redrover"
    wave = "W6"
    kind = "ats"
    tenant = True
    hosts = (HOST, "api.redroverk12.com")

    def detect(self, careers_url: str):
        o = _org(careers_url)
        return Target(slug=o, careers_url=f"https://{HOST}/org/{o}", api_url=API) if o else None

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        org = target.slug or _org(target.careers_url)
        if not org:
            raise ProviderError("redrover: need https://jobs.redroverk12.com/org/<id>")
        data = ctx.http.post_json(API, {
            "operationName": "GetJobPostings",
            "variables": {"search": {"orgId": org, "searchTerm": "", "locationIds": [], "jobPostingCategoryIds": []}},
            "query": QUERY}, headers={"Origin": f"https://{HOST}"})
        if not isinstance(data, dict):
            return []
        if data.get("errors"):
            raise ProviderError(f"redrover: API error: {(data['errors'][0] or {}).get('message', 'unknown')}")
        site = (data.get("data") or {}).get("jobSeekerSiteUnauthenticated")
        if site is None:
            return []
        search = site.get("jobPostingSearch")
        if not isinstance(search, dict):
            raise ProviderError("redrover: unexpected response shape")
        if search.get("hasMoreData"):
            ctx.warn("redrover: more postings than one response holds")
        jobs: list[Job] = []
        for j in search.get("results") or []:
            jid, title = str((j or {}).get("id") or "").strip(), str(j.get("name") or "").strip()
            if not re.fullmatch(r"\d+", jid) or not title:
                continue
            if not j.get("activePublicOnDateUtc") or j.get("closedOnDateUtc"):
                continue
            where = " - ".join(x for x in [(j.get("location") or {}).get("name"), j.get("organizationName")] if x)
            jobs.append(self.job(
                title=title, url=f"https://{HOST}/org/{org}/opening/{jid}", company=target.company or j.get("organizationName") or org,
                location=where, workplace="remote" if j.get("allowsRemote") else "",
                posted_at=to_iso(j["activePublicOnDateUtc"]), source_id=jid).validate())
            if len(jobs) >= ctx.max_jobs:
                break
        return jobs


PROVIDER = RedRover()
