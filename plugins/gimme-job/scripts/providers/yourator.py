"""Yourator (Taiwan startup jobs) — public jobs API, board-wide.

GET https://www.yourator.co/api/v4/jobs?page=N → payload.jobs[], payload.hasMore
Mechanism from career-ops providers/yourator.mjs (MIT); code is our own.
"""
from __future__ import annotations

from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit, urlunsplit

from ._base import Context, Job, Provider, ProviderError, Target

ORIGIN = "https://www.yourator.co"
FEED = ORIGIN + "/api/v4/jobs"
HOST = "www.yourator.co"


def resolve_url(j: dict) -> str:
    raw = (j.get("thirdPartyUrl") or "").strip()
    p = urlsplit(raw)
    if raw and p.scheme == "https" and p.netloc:
        q = [(k, v) for k, v in parse_qsl(p.query, keep_blank_values=True) if not k.lower().startswith("utm_")]
        return urlunsplit((p.scheme, p.netloc, p.path, urlencode(q), p.fragment))
    path = (j.get("path") or "").strip()
    if not path.startswith("/") or path.startswith(("//", "/\\")):
        return ""
    u = urljoin(ORIGIN, path)
    return u if urlsplit(u).netloc == HOST else ""


class Yourator(Provider):
    name = "yourator"
    wave = "W5"
    kind = "board"
    tenant = False
    hosts = (HOST,)

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        max_pages = min(int(target.options.get("max_pages") or 120), 500)
        out: list[Job] = []
        for page in range(1, max_pages + 1):
            data = ctx.http.get_json(f"{FEED}?page={page}")
            jobs = ((data or {}).get("payload") or {}).get("jobs")
            if not isinstance(jobs, list):
                raise ProviderError("yourator: unexpected response, expected {payload: {jobs: [...]}}")
            for j in jobs:
                title = (j.get("name") or "").strip()
                url = resolve_url(j)
                if not title or not url:
                    continue
                loc = (j.get("location") or "").strip() if isinstance(j.get("location"), str) else ""
                out.append(self.job(
                    title=title, url=url, company=((j.get("company") or {}).get("brand") or "").strip(),
                    location=loc, locations=[loc] if loc else [], country="TW",
                    source_id=str(j.get("id") or ""),
                ).validate())
                if len(out) >= ctx.max_jobs:
                    return out
            if data["payload"].get("hasMore") is not True:
                break
        return out


PROVIDER = Yourator()
