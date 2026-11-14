"""Garena — POST https://careers.garena.com/api/job/list?office=<office>.

Mechanism from career-ops providers/garena.mjs (MIT); code is our own.
"""
from __future__ import annotations

from urllib.parse import quote, urlsplit

from ._base import Context, Job, Provider, ProviderError, Target
from ._parse import html_to_text

HOST = "careers.garena.com"


class Garena(Provider):
    name = "garena"
    wave = "W6"
    kind = "company"
    tenant = False
    hosts = (HOST,)

    def detect(self, careers_url: str):
        if urlsplit(careers_url or "").netloc.lower() == HOST:
            return Target(careers_url=careers_url)
        return None

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        office = str(target.options.get("office") or "global").strip()
        if office in (".", ".."):
            raise ProviderError("garena: bad office")
        seg = quote(office, safe="")
        data = ctx.http.post_json(f"https://{HOST}/api/job/list?office={seg}", {})
        rows = data.get("jobs") if isinstance(data, dict) else None
        if not isinstance(rows, list):
            raise ProviderError("garena: unexpected response, expected jobs[]")
        jobs: list[Job] = []
        for j in rows:
            title = str((j or {}).get("title") or "").strip()
            jid = str(j.get("id") if j and j.get("id") is not None else "").strip()
            if not title or not jid or jid in (".", ".."):
                continue
            locs = [l for l in ((j.get("tags") or {}).get("location") or []) if isinstance(l, str) and l.strip()]
            jobs.append(self.job(title=title, url=f"https://{HOST}/{seg}/careers/{quote(jid, safe='')}",
                                 company=target.company or "Garena", locations=locs,
                                 description=html_to_text(j.get("description") or ""),
                                 source_id=jid).validate())
            if len(jobs) >= ctx.max_jobs:
                break
        return jobs


PROVIDER = Garena()
