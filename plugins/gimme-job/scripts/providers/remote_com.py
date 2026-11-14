"""Remote.com own jobs board (apply.remote.com) — public JSON API, one request.

GET https://apply.remote.com/api/public/jobs -> {jobs: [{public_id, title, location, workplace, opened_at, status}]}
Mechanism from career-ops providers/remote-com.mjs (MIT); code is our own.
"""
from __future__ import annotations

from urllib.parse import quote, urlsplit

from ._base import Context, Job, Provider, ProviderError, Target
from ._parse import to_iso, workplace_from

HOST = "apply.remote.com"
API = f"https://{HOST}/api/public/jobs"
REGIONS = {"EMEA": "Europe, Middle East & Africa", "NORAM": "North America",
           "LATAM": "Latin America", "APAC": "Asia-Pacific"}
WP_LABEL = {"remote": "Remote", "hybrid": "Hybrid", "onsite": "On-site"}


def _location(loc, workplace) -> str:
    regions, seen = [], set()
    for raw in str(loc or "").split(","):
        code = raw.strip()
        if not code or code.upper() in seen:
            continue
        seen.add(code.upper())
        name = REGIONS.get(code.upper())
        regions.append(f"{code.upper()} ({name})" if name else code)
    wp = WP_LABEL.get(workplace_from(workplace), "")
    return " · ".join(x for x in (wp, " / ".join(regions)) if x)


class RemoteCom(Provider):
    name = "remote-com"
    wave = "W3"
    kind = "company"
    tenant = False
    hosts = (HOST,)

    def detect(self, careers_url: str):
        if urlsplit(careers_url or "").netloc.lower() == HOST:
            return Target(company="Remote", careers_url=careers_url, api_url=API)
        return None

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        data = ctx.http.get_json(API)
        rows = data.get("jobs") if isinstance(data, dict) else None
        if not isinstance(rows, list):
            raise ProviderError("remote-com: expected jobs[]")
        jobs: list[Job] = []
        for r in rows:
            if not isinstance(r, dict) or r.get("accepting_applications") is False or r.get("status") == "closed":
                continue
            title = (r.get("title") or "").strip()
            pid = (r.get("public_id") or "").strip()
            if not title or not pid:
                continue
            jobs.append(self.job(
                title=title, url=f"https://{HOST}/jobs/{quote(pid, safe='')}", company="Remote",
                location=_location(r.get("location"), r.get("workplace")),
                workplace=workplace_from(r.get("workplace")),
                posted_at=to_iso(r.get("opened_at")), source_id=pid,
            ).validate())
            if len(jobs) >= ctx.max_jobs:
                break
        return jobs


PROVIDER = RemoteCom()
