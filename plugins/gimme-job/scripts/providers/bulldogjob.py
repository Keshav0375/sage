"""Bulldogjob (PL) — Next.js listing pages; jobs are in __NEXT_DATA__ props.pageProps.jobs.

GET https://bulldogjob.pl/companies/jobs/s/page,N
Mechanism from career-ops providers/bulldogjob.mjs (MIT); code is our own.
"""
from __future__ import annotations

from urllib.parse import quote

from ._base import Context, Job, Provider, ProviderError, Target
from ._parse import next_data

ORIGIN = "https://bulldogjob.pl"
PAGE_SIZE = 50


class Bulldogjob(Provider):
    name = "bulldogjob"
    wave = "W5"
    kind = "board"
    tenant = False
    hosts = ("bulldogjob.pl",)

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        pages = min(int(target.options.get("max_pages") or 5), 100)
        kw = (target.query or "").lower().split()
        jobs: list[Job] = []
        seen: set[str] = set()
        for page in range(1, pages + 1):
            html = ctx.http.get_text(f"{ORIGIN}/companies/jobs/s/page,{page}")
            pp = ((next_data(html) or {}).get("props") or {}).get("pageProps") or {}
            rows = pp.get("jobs")
            if not isinstance(rows, list):
                raise ProviderError("bulldogjob: no props.pageProps.jobs in listing page")
            for j in rows:
                jid = str(j.get("id") or "").strip()
                title = str(j.get("position") or "").strip()
                if not jid or not title:
                    continue
                if kw and not all(w in title.lower() for w in kw):
                    continue
                url = str(j.get("redirectTo") or "").strip()
                if not url.startswith("https://"):
                    url = f"{ORIGIN}/companies/jobs/{quote(jid, safe='')}"
                if url in seen:
                    continue
                seen.add(url)
                city = str(j.get("city") or "").strip()
                jobs.append(self.job(
                    title=title, url=url,
                    company=str((j.get("company") or {}).get("name") or "").strip(),
                    location=city, country="PL",
                    workplace="remote" if j.get("remote") is True else "",
                    source_id=jid,
                    extra={"language": j.get("locale") or ""},
                ).validate())
                if len(jobs) >= ctx.max_jobs:
                    return jobs
            if len(rows) < PAGE_SIZE:
                break
        return jobs


PROVIDER = Bulldogjob()
