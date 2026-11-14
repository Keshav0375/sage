"""Gem job boards — jobs.gem.com public GraphQL batch endpoint (or the api.gem.com REST job_posts feed).

Mechanism from career-ops providers/gem.mjs (MIT).
"""
from __future__ import annotations

import re
from urllib.parse import urlsplit

from ._base import Context, Job, Provider, ProviderError, Target
from ._parse import html_to_text, to_iso, workplace_from, employment_from

GQL = "https://jobs.gem.com/api/public/graphql/batch"
LIST_Q = """query JobBoardList($boardId: String!) {
  oatsExternalJobPostings(boardId: $boardId) {
    jobPostings { id extId title
      locations { id name city isoCountry isRemote extId __typename }
      job { id department { id name extId __typename } locationType employmentType __typename }
      __typename }
    __typename } }
"""
DETAIL_Q = """query ExternalJobPostingQuery($boardId: String!, $extId: String!) {
  oatsExternalJobPosting(boardId: $boardId, extId: $extId) {
    extId firstPublishedTsSec descriptionHtml jobPostSectionHtml { introHtml outroHtml } compensationHtml __typename } }
"""
HEADERS = {"batch": "true"}


def _board(url: str) -> str:
    p = urlsplit(url or "")
    if p.netloc.lower() != "jobs.gem.com":
        return ""
    m = re.match(r"^/([^/?#]+)", p.path)
    return m.group(1) if m else ""


def _loc(l: dict) -> str:
    place = (l.get("name") or "").strip()
    return " · ".join(x for x in (place, "Remote" if l.get("isRemote") else "") if x)


class Gem(Provider):
    name = "gem"
    wave = "W2"
    kind = "ats"
    tenant = True
    hosts = ("jobs.gem.com", "api.gem.com")

    def detect(self, careers_url: str):
        p = urlsplit(careers_url or "")
        if p.scheme == "https" and p.netloc.lower() == "api.gem.com" and re.match(r"^/job_board/v0/[^/?#]+/job_posts/?$", p.path):
            return Target(slug=p.path.split("/")[3], careers_url=careers_url, api_url=careers_url)
        b = _board(careers_url)
        return Target(slug=b, careers_url=careers_url, api_url=GQL) if b else None

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        company = target.company or target.slug
        if urlsplit(target.api_url or "").netloc.lower() == "api.gem.com":
            return self._rest(ctx.http.get_json(target.api_url), company, ctx)
        board = target.slug or _board(target.careers_url)
        if not board:
            raise ProviderError("gem needs a jobs.gem.com/<board> url")
        res = ctx.http.post_json(GQL, [{"operationName": "JobBoardList", "variables": {"boardId": board}, "query": LIST_Q}], headers=HEADERS)
        first = (res or [{}])[0]
        if first.get("errors"):
            raise ProviderError(f"gem: JobBoardList failed: {first['errors'][0].get('message', 'unknown')}")
        postings = [p for p in (((first.get("data") or {}).get("oatsExternalJobPostings") or {}).get("jobPostings") or [])
                    if p.get("extId") and p.get("title")][: ctx.max_jobs]
        detail: dict[str, dict] = {}
        if postings:
            try:
                dres = ctx.http.post_json(GQL, [{"operationName": "ExternalJobPostingQuery",
                                                 "variables": {"boardId": board, "extId": p["extId"]}, "query": DETAIL_Q} for p in postings],
                                          headers=HEADERS)
                for d in dres or []:
                    x = ((d or {}).get("data") or {}).get("oatsExternalJobPosting")
                    if x and x.get("extId"):
                        detail[x["extId"]] = x
            except ProviderError:
                pass
        jobs = []
        for p in postings:
            d = detail.get(p["extId"], {})
            sec = d.get("jobPostSectionHtml") or {}
            desc = "\n\n".join(x for x in (html_to_text(sec.get("introHtml")), html_to_text(d.get("descriptionHtml")),
                                           html_to_text(sec.get("outroHtml"))) if x)
            job = p.get("job") or {}
            locs = list(dict.fromkeys(x for x in (_loc(l) for l in p.get("locations") or []) if x))
            jobs.append(self.job(title=p["title"], url=f"https://jobs.gem.com/{board}/{p['extId']}", company=company,
                                 locations=locs, description=desc, posted_at=to_iso(d.get("firstPublishedTsSec")),
                                 workplace=workplace_from(job.get("locationType")),
                                 employment=employment_from(job.get("employmentType")),
                                 department=((job.get("department") or {}).get("name") or ""),
                                 source_id=str(p["extId"])).validate())
        return jobs

    def _rest(self, data, company, ctx) -> list[Job]:
        rows = data if isinstance(data, list) else ((data or {}).get("job_posts") if isinstance(data, dict) else None)
        if rows is None:
            raise ProviderError("gem: unsupported REST envelope")
        jobs = []
        for j in rows[: ctx.max_jobs]:
            u = urlsplit(j.get("absolute_url") or "")
            if u.scheme != "https" or u.netloc.lower() != "jobs.gem.com" or not (j.get("title") or "").strip():
                continue
            loc = j.get("location") or {}
            jobs.append(self.job(title=j["title"], url=j["absolute_url"], company=company, location=_loc(loc) if isinstance(loc, dict) else "",
                                 description=(j.get("content_plain") or html_to_text(j.get("content") or "")).strip(),
                                 posted_at=to_iso(j.get("first_published_at")), source_id=str(j.get("id") or "")).validate())
        return jobs


PROVIDER = Gem()
