"""Jobicy — public remote-jobs API (no auth).

GET https://jobicy.com/api/v2/remote-jobs?count=100[&geo=&industry=&tag=&cursor=]
Mechanism from career-ops providers/jobicy.mjs (MIT); code is our own.
Filters come from Target.options (geo, industry, tag); Target.query is used as tag.
"""
from __future__ import annotations

import html
import re
from urllib.parse import urlencode, urlsplit

from ._base import Context, Job, Provider, ProviderError, Target
from ._parse import employment_from, html_to_text, to_iso

FEED = "https://jobicy.com/api/v2/remote-jobs"
SLUG = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")


class Jobicy(Provider):
    name = "jobicy"
    wave = "W1"
    kind = "board"
    tenant = False
    hosts = ("jobicy.com",)

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        params: dict[str, str] = {"count": "100"}
        for k in ("geo", "industry"):
            v = str(target.options.get(k, "")).strip().lower()
            if v:
                if not SLUG.match(v):
                    raise ProviderError(f"jobicy: {k} {v!r} is not a slug")
                params[k] = v
        tag = str(target.options.get("tag") or target.query or "").strip()
        if tag:
            params["tag"] = tag
        max_pages = int(target.options.get("max_pages", 25))
        jobs: list[Job] = []
        seen: set[str] = set()
        cursor = ""
        for _ in range(max_pages):
            q = dict(params, **({"cursor": cursor} if cursor else {}))
            data = ctx.http.get_json(f"{FEED}?{urlencode(q)}")
            rows = data.get("jobs") if isinstance(data, dict) else None
            if not isinstance(rows, list):
                raise ProviderError("jobicy: expected {jobs: [...]}")
            for j in rows:
                title = html.unescape(str(j.get("jobTitle") or "")).strip()
                p = urlsplit(str(j.get("url") or "").strip())
                url = p.geturl()
                if not title or p.scheme != "https" or p.netloc not in ("jobicy.com", "www.jobicy.com") or url in seen:
                    continue
                seen.add(url)
                et = j.get("jobType")
                et = et[0] if isinstance(et, list) and et else et
                extra = {}
                lo, hi = j.get("salaryMin") or j.get("annualSalaryMin"), j.get("salaryMax") or j.get("annualSalaryMax")
                if isinstance(lo, (int, float)) and isinstance(hi, (int, float)) and hi > 0:
                    extra = dict(salary_min=float(lo), salary_max=float(hi),
                                 currency=j.get("salaryCurrency") or "", salary_period="year")
                lvl = j.get("jobIndustry")
                jobs.append(self.job(
                    title=title, url=url, company=html.unescape(str(j.get("companyName") or "")).strip(),
                    location=html.unescape(str(j.get("jobGeo") or "")).strip(), workplace="remote",
                    employment=employment_from(et), department=html.unescape(lvl[0]) if isinstance(lvl, list) and lvl else "",
                    posted_at=to_iso(j.get("pubDate")), description=html_to_text(j.get("jobDescription") or ""),
                    source_id=str(j.get("id", "")), **extra,
                ).validate())
            nxt = data.get("nextCursor") if isinstance(data.get("nextCursor"), str) else ""
            if not nxt or data.get("hasMore") is False or not rows or len(jobs) >= ctx.max_jobs:
                break
            if nxt == cursor:
                break
            cursor = nxt
        return jobs[: ctx.max_jobs]


PROVIDER = Jobicy()
