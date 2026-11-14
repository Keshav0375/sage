"""Gupy (BR) — portal job-search JSON API (board-wide, keyword driven).

GET https://portal.gupy.io/api/job-search/jobs?jobName=<kw>&offset=N&limit=100
Mechanism from career-ops providers/gupy.mjs (MIT); code is our own.
Drops confidential-employer postings, like upstream.
"""
from __future__ import annotations

import re
from urllib.parse import urlencode, urlsplit

from ._base import Context, Job, Provider, ProviderError, Target
from ._parse import to_iso

API = "https://portal.gupy.io/api/job-search/jobs"
PER_PAGE = 100
CONFIDENTIAL = re.compile(r"^(?:empresa\s+)?confidencial$", re.I)
WP = {"remote": ("remote", "Remoto"), "hybrid": ("hybrid", "Híbrido"), "on-site": ("onsite", "Presencial")}


def _safe(url: str) -> bool:
    p = urlsplit(url or "")
    h = p.netloc.lower()
    return p.scheme == "https" and (h == "gupy.io" or h.endswith(".gupy.io"))


class Gupy(Provider):
    name = "gupy"
    wave = "W5"
    kind = "board"
    tenant = False
    hosts = ("portal.gupy.io", "gupy.io")

    def detect(self, careers_url: str):
        h = urlsplit(careers_url or "").netloc.lower()
        if h in ("portal.gupy.io", "employability-portal.gupy.io"):
            return Target(careers_url=careers_url, api_url=API)
        return None

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        kws = target.options.get("keywords") or [k.strip() for k in (target.query or "").split(",") if k.strip()]
        if isinstance(kws, str):
            kws = [kws]
        if not kws:
            raise ProviderError("gupy needs keywords (target.query or options.keywords)")
        pages = min(int(target.options.get("max_pages") or 3), 100)
        seen: dict[str, Job] = {}
        for kw in kws:
            for page in range(pages):
                params = {"jobName": kw, "offset": page * PER_PAGE, "limit": PER_PAGE}
                if target.options.get("workplace_types"):
                    params["workplaceType"] = ",".join(target.options["workplace_types"])
                if target.location:
                    params["state"] = target.location
                data = ctx.http.get_json(f"{API}?{urlencode(params)}")
                rows = (data or {}).get("data") if isinstance(data, dict) else None
                if not isinstance(rows, list):
                    raise ProviderError(f"gupy: unexpected response for {kw!r}, expected {{data: [...]}}")
                for j in rows:
                    title = str(j.get("name") or "").strip()
                    url = str(j.get("jobUrl") or "").strip()
                    company = str(j.get("careerPageName") or "").strip()
                    if (j.get("isConfidentialCareerPage") is True or not title or not _safe(url) or not company
                            or CONFIDENTIAL.match(company) or url in seen
                            or str(j.get("careerPageLogo") or "").endswith("/confidencial_logo.png")):
                        continue
                    wp = WP.get(str(j.get("workplaceType") or "").strip())
                    parts = [str(j.get(k)).strip() for k in ("city", "state", "country") if j.get(k)]
                    seen[url] = self.job(
                        title=title, url=url, company=company, location=", ".join(parts),
                        country="BR" if str(j.get("country") or "").lower() in ("brasil", "brazil") else "",
                        workplace=(wp[0] if wp else ("remote" if j.get("isRemoteWork") is True else "")),
                        posted_at=to_iso(j.get("publishedDate")),
                        description=str(j.get("description") or ""),
                        source_id=str(j.get("id") or ""),
                    ).validate()
                    if len(seen) >= ctx.max_jobs:
                        return list(seen.values())
                if len(rows) < PER_PAGE:
                    break
        return list(seen.values())


PROVIDER = Gupy()
