"""Flowxtra — board-wide: GET https://app.flowxtra.com/api/central/jobs?status=Live&per_page=100&page=N.

Mechanism from career-ops providers/flowxtra.mjs (MIT); code is our own.
"""
from __future__ import annotations

from urllib.parse import urlsplit

from ._base import Context, Job, Provider, ProviderError, Target
from ._parse import to_iso

ENDPOINT = "https://app.flowxtra.com/api/central/jobs"
PER_PAGE = 100
MAX_PAGES = 3


def _s(v) -> str:
    return v.strip() if isinstance(v, str) else ""


class Flowxtra(Provider):
    name = "flowxtra"
    wave = "W4"
    kind = "board"
    tenant = False
    hosts = ("app.flowxtra.com", "flowxtra.com")

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        pages = target.options.get("max_pages") if target.options else None
        pages = pages if isinstance(pages, int) and 0 < pages <= 50 else MAX_PAGES
        jobs: list[Job] = []
        for page in range(1, pages + 1):
            data = ctx.http.get_json(f"{ENDPOINT}?status=Live&per_page={PER_PAGE}&page={page}")
            rows = ((data or {}).get("data") or {}).get("data") if isinstance(data, dict) else None
            if not isinstance(rows, list):
                raise ProviderError(f"flowxtra: unexpected response on page {page}, expected data.data[]")
            for j in rows:
                if not isinstance(j, dict) or not _s(j.get("title")):
                    continue
                url = _s(j.get("urlJobApplay"))
                u = urlsplit(url)
                if u.scheme != "https" or (u.hostname or "").lower() != "flowxtra.com":
                    continue
                parts = [_s(j.get(k)) for k in ("city_company", "state_company", "country_company")]
                parts = [p for p in parts if p]
                remote = j.get("workplace") == "Remote"
                if remote:
                    parts.append("Remote")
                jobs.append(self.job(
                    title=_s(j["title"]), url=url, company=_s(j.get("name_company")) or target.company or "Flowxtra",
                    location=", ".join(parts), workplace="remote" if remote else "",
                    posted_at=to_iso(j.get("date_share")), source_id=str(j.get("id", "")),
                ).validate())
                if len(jobs) >= ctx.max_jobs:
                    return jobs
            if not (data["data"].get("next_page_url")) or len(rows) < PER_PAGE:
                break
        return jobs


PROVIDER = Flowxtra()
