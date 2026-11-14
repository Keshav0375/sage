"""Get on Board — public JSON:API per category.

GET https://www.getonbrd.com/api/v0/categories/<category>/jobs?per_page=100&expand[]=company&page=N
Mechanism from career-ops providers/getonbrd.mjs (MIT); code is our own.
"""
from __future__ import annotations

import re

from ._base import Context, Job, Provider, ProviderError, Target
from ._parse import to_iso

BASE = "https://www.getonbrd.com/api/v0/categories/{cat}/jobs"
SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
PER_PAGE = 100


class GetOnBoard(Provider):
    name = "getonbrd"
    wave = "W5"
    kind = "board"
    tenant = False
    hosts = ("www.getonbrd.com",)

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        cats = target.options.get("categories") or target.options.get("category") or ["programming"]
        if isinstance(cats, str):
            cats = [cats]
        pages = min(int(target.options.get("max_pages") or 3), 50)
        kw = (target.query or "").lower().split()
        jobs: list[Job] = []
        seen: set[str] = set()
        for cat in cats:
            if not SLUG.match(str(cat)):
                raise ProviderError(f"getonbrd: invalid category {cat!r}")
            for page in range(1, pages + 1):
                data = ctx.http.get_json(f"{BASE.format(cat=cat)}?per_page={PER_PAGE}&expand[]=company&page={page}")
                rows = (data or {}).get("data")
                if not isinstance(rows, list):
                    raise ProviderError("getonbrd: unexpected response, expected {data: [...]}")
                for j in rows:
                    a = j.get("attributes") or {}
                    title = str(a.get("title") or "").strip()
                    url = str((j.get("links") or {}).get("public_url") or "").strip()
                    if not title or not url.startswith("https://") or url in seen:
                        continue
                    if kw and not all(w in title.lower() for w in kw):
                        continue
                    seen.add(url)
                    countries = a.get("countries")
                    if isinstance(countries, str):
                        countries = [countries]
                    countries = [c.strip() for c in countries or [] if isinstance(c, str) and c.strip()]
                    name = ((a.get("company") or {}).get("data") or {}).get("attributes", {}).get("name") or ""
                    jobs.append(self.job(
                        title=title, url=url, company=str(name).strip(),
                        location="Remote" if a.get("remote") is True else ", ".join(countries),
                        locations=countries,
                        workplace="remote" if a.get("remote") is True else "",
                        posted_at=to_iso(a.get("published_at")),
                        source_id=str(j.get("id") or ""),
                    ).validate())
                    if len(jobs) >= ctx.max_jobs:
                        return jobs
                if len(rows) < PER_PAGE:
                    break
        return jobs


PROVIDER = GetOnBoard()
