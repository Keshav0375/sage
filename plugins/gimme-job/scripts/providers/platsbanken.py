"""Platsbanken (Sweden, Arbetsformedlingen) via the open JobTech search API, board-wide.

GET https://jobsearch.api.jobtechdev.se/search?q=<kw>&limit=100&offset=N
Mechanism from career-ops providers/platsbanken.mjs (MIT); code is our own.
"""
from __future__ import annotations

from urllib.parse import quote, urlencode

from ._base import Context, Job, Provider, ProviderError, Target
from ._parse import to_iso

SEARCH = "https://jobsearch.api.jobtechdev.se/search"
POSTING = "https://arbetsformedlingen.se/platsbanken/annonser/"
PAGE = 100


def _keywords(target: Target) -> list[str]:
    raw = target.options.get("keywords") or target.options.get("queries") or target.query
    if isinstance(raw, str):
        raw = raw.replace("\n", ",").split(",")
    return list(dict.fromkeys(str(x).strip() for x in raw or [] if str(x).strip()))


def _location(addr: dict) -> str:
    parts, seen = [], set()
    for v in ((addr.get("city") or addr.get("municipality") or ""), addr.get("region") or "", addr.get("country") or ""):
        v = str(v).strip()
        if v and v.lower() not in seen:
            seen.add(v.lower())
            parts.append(v)
    return ", ".join(parts)


class Platsbanken(Provider):
    name = "platsbanken"
    wave = "W5"
    kind = "board"
    tenant = False
    hosts = ("jobsearch.api.jobtechdev.se", "arbetsformedlingen.se")

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        kws = _keywords(target)
        if not kws:
            raise ProviderError("platsbanken needs target.query / options.keywords")
        max_pages = min(int(target.options.get("max_pages") or 5), 21)
        jobs: dict[str, Job] = {}
        for kw in kws:
            for page in range(max_pages):
                data = ctx.http.get_json(f"{SEARCH}?{urlencode({'q': kw, 'limit': PAGE, 'offset': page * PAGE})}")
                hits = (data or {}).get("hits")
                if not isinstance(hits, list):
                    raise ProviderError("platsbanken: unexpected response, expected hits[]")
                for h in hits:
                    jid = str(h.get("id") or "").strip()
                    title = (h.get("headline") or "").strip()
                    if not jid or not title or jid in jobs:
                        continue
                    addr = h.get("workplace_address") or {}
                    loc = _location(addr)
                    jobs[jid] = self.job(
                        title=title, url=POSTING + quote(jid, safe=""),
                        company=((h.get("employer") or {}).get("name") or "").strip(),
                        location=loc, locations=[loc] if loc else [], country="SE",
                        description=((h.get("description") or {}).get("text") or "").strip(),
                        posted_at=to_iso(h.get("publication_date")),
                        closes_at=to_iso(h.get("application_deadline")), source_id=jid,
                    ).validate()
                    if len(jobs) >= ctx.max_jobs:
                        return list(jobs.values())
                if len(hits) < PAGE:
                    break
        return list(jobs.values())


PROVIDER = Platsbanken()
