"""Dover — public careers-page API: app.dover.com/api/v1/careers-page/<board-uuid>/jobs.

Mechanism from career-ops providers/dover.mjs (MIT).
"""
from __future__ import annotations

import re
from urllib.parse import quote, unquote, urlsplit

from ._base import Context, Job, Provider, ProviderError, Target

HOST = "app.dover.com"
UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.I)
PAGE_SIZE = 300
MAX_PAGES = 5


def _board(url: str):
    p = urlsplit(url or "")
    if p.scheme != "https" or p.netloc.lower() != HOST:
        return None
    segs = [s for s in p.path.split("/") if s]
    if len(segs) < 3 or segs[1] != "careers" or not UUID_RE.match(segs[2]):
        return None
    return unquote(segs[0]), segs[2].lower()


def _loc(l: dict) -> str:
    opt = l.get("location_option") or {}
    place = next((str(v).strip() for v in (opt.get("display_name"), l.get("name")) if isinstance(v, str) and v.strip()), "")
    t = str(l.get("location_type") or "").upper()
    if t == "REMOTE":
        return f"Remote ({place})" if place else "Remote"
    if t == "HYBRID":
        return f"{place} (Hybrid)" if place else "Hybrid"
    return place


class Dover(Provider):
    name = "dover"
    wave = "W2"
    kind = "ats"
    tenant = True
    hosts = ("app.dover.com",)

    def detect(self, careers_url: str):
        b = _board(careers_url)
        if not b:
            return None
        return Target(company=b[0], slug=b[1], careers_url=careers_url,
                      api_url=f"https://{HOST}/api/v1/careers-page/{b[1]}/jobs")

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        b = _board(target.careers_url)
        if not b and UUID_RE.match(target.slug or ""):
            b = (target.company, target.slug.lower())
        if not b:
            raise ProviderError("dover needs an app.dover.com/<company>/careers/<uuid> url")
        jobs: list[Job] = []
        for page in range(MAX_PAGES):
            data = ctx.http.get_json(f"https://{HOST}/api/v1/careers-page/{b[1]}/jobs?limit={PAGE_SIZE}&offset={page * PAGE_SIZE}")
            if not isinstance(data, dict) or not isinstance(data.get("results"), list):
                raise ProviderError("dover: unexpected response, no results[]")
            for j in data["results"]:
                title = (j.get("title") or "").strip()
                if j.get("is_published") is False or j.get("is_sample") is True or not title or not j.get("id"):
                    continue
                locs = sorted(j.get("locations") or [], key=lambda l: not (l or {}).get("is_primary"))
                places = list(dict.fromkeys(x for x in (_loc(l) for l in locs if isinstance(l, dict)) if x))
                if not places and str(j.get("workplace_type") or "").upper() == "REMOTE":
                    places = ["Remote"]
                jobs.append(self.job(title=title, url=f"https://{HOST}/apply/{quote(b[0])}/{quote(str(j['id']), safe='')}",
                                     company=target.company or b[0], locations=places,
                                     workplace="remote" if str(j.get("workplace_type") or "").upper() == "REMOTE" else "",
                                     source_id=str(j["id"])).validate())
                if len(jobs) >= ctx.max_jobs:
                    return jobs
            if len(data["results"]) < PAGE_SIZE or not data.get("next"):
                break
        return jobs


PROVIDER = Dover()
