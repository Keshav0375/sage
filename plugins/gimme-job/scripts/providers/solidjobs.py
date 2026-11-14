"""Solid.Jobs (Poland) — public offers API per division, board-wide.

GET https://solid.jobs/public-api/offers/<division>   (division from options.division / target.query, default "it")
Mechanism from career-ops providers/solidjobs.mjs (MIT); code is our own.
"""
from __future__ import annotations

from urllib.parse import quote, urlsplit

from ._base import Context, Job, Provider, ProviderError, Target

BASE = "https://solid.jobs/public-api/offers/"


class SolidJobs(Provider):
    name = "solidjobs"
    wave = "W5"
    kind = "board"
    tenant = False
    hosts = ("solid.jobs",)

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        url = target.api_url or target.careers_url
        if not url:
            division = (target.options.get("division") or target.query or "it").strip()
            url = BASE + quote(division, safe="")
            if target.options.get("campaign"):
                url += "?campaign=" + quote(str(target.options["campaign"]))
        p = urlsplit(url)
        if p.scheme != "https" or p.netloc != "solid.jobs" or not p.path.startswith("/public-api/offers/"):
            raise ProviderError(f"solidjobs: untrusted url {url}")
        data = ctx.http.get_json(url)
        if not isinstance(data, dict) or not isinstance(data.get("jobs"), list):
            raise ProviderError("solidjobs: unexpected response, expected {jobs: [...]}")
        out: list[Job] = []
        for j in data["jobs"][: ctx.max_jobs]:
            if not isinstance(j, dict) or not str(j.get("url") or "").strip():
                continue
            locs = j.get("locations")
            locs = [str(x) for x in locs] if isinstance(locs, list) else ([locs] if isinstance(locs, str) and locs else [])
            out.append(self.job(title=j.get("title") or "", url=str(j["url"]).strip(),
                                company=j.get("company") or target.company, locations=locs,
                                country="PL").validate())
        return out


PROVIDER = SolidJobs()
