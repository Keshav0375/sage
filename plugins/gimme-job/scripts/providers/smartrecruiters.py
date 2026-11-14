"""SmartRecruiters — public postings API (no auth).

GET https://api.smartrecruiters.com/v1/companies/{slug}/postings?limit=100&offset=N
Mechanism from career-ops providers/smartrecruiters.mjs (MIT); code is our own.
"""
from __future__ import annotations

import re
from urllib.parse import quote, urlsplit

from ._base import Context, Job, Provider, ProviderError, Target
from ._parse import employment_from, to_iso

PAGE = 100


def _slugify(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", (s or "").lower()).strip("-")


class SmartRecruiters(Provider):
    name = "smartrecruiters"
    wave = "W1"
    kind = "ats"
    tenant = True
    hosts = ("smartrecruiters.com",)

    def detect(self, careers_url: str):
        p = urlsplit(careers_url or "")
        if p.netloc.lower() not in ("careers.smartrecruiters.com", "jobs.smartrecruiters.com"):
            return None
        parts = [x for x in p.path.split("/") if x]
        if not parts:
            return None
        return Target(slug=parts[0], careers_url=careers_url,
                      api_url=f"https://api.smartrecruiters.com/v1/companies/{parts[0]}/postings")

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        slug = target.slug or (self.detect(target.careers_url) or Target()).slug
        if not slug:
            raise ProviderError("smartrecruiters needs a company slug")
        out: list[Job] = []
        offset = 0
        while len(out) < ctx.max_jobs:
            url = f"https://api.smartrecruiters.com/v1/companies/{slug}/postings?limit={PAGE}&offset={offset}&status=PUBLIC"
            data = ctx.http.get_json(url)
            items = data.get("content") if isinstance(data, dict) else None
            if not isinstance(items, list):
                raise ProviderError("smartrecruiters: expected content[]")
            for j in items:
                pid = str(j.get("id", ""))
                name = j.get("name", "")
                if not pid or not name:
                    continue
                loc = j.get("location") or {}
                full = loc.get("fullLocation") or ", ".join(x for x in (loc.get("city"), loc.get("region"), (loc.get("country") or "").upper()) if x)
                wp = "remote" if loc.get("remote") else ("hybrid" if loc.get("hybrid") else "")
                slug_ = _slugify(name)
                out.append(self.job(
                    title=name,
                    url=f"https://jobs.smartrecruiters.com/{slug}/{quote(pid)}" + (f"-{slug_}" if slug_ else ""),
                    company=target.company or (j.get("company") or {}).get("name") or slug,
                    location=full, country=(loc.get("country") or "").upper(), workplace=wp,
                    employment=employment_from((j.get("typeOfEmployment") or {}).get("label")),
                    department=(j.get("department") or {}).get("label", ""),
                    posted_at=to_iso(j.get("releasedDate")), source_id=pid,
                ).validate())
            offset += PAGE
            total = data.get("totalFound")
            if len(items) < PAGE or (isinstance(total, int) and offset >= total):
                break
        return out[: ctx.max_jobs]


PROVIDER = SmartRecruiters()
