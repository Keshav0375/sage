"""Arbeitsagentur Jobsuche — German federal job search REST API (public client key).

GET https://rest.arbeitsagentur.de/jobboerse/jobsuche-service/pc/v6/jobs?was=<kw>&wo=<place>
Mechanism from career-ops providers/arbeitsagentur.mjs (MIT); code is our own.
Simplified: single page per keyword, no remote-nationwide second pass.
"""
from __future__ import annotations

from urllib.parse import quote, urlencode

from ._base import Context, Job, Provider, ProviderError, Target

API = "https://rest.arbeitsagentur.de/jobboerse/jobsuche-service/pc/v6/jobs"
API_KEY = "jobboerse-jobsuche"
DETAIL = "https://www.arbeitsagentur.de/jobsuche/jobdetail/"


def _location(lokationen) -> str:
    places: list[str] = []
    for e in lokationen or []:
        a = (e or {}).get("adresse") or {}
        ort = str(a.get("ort") or "").strip()
        land = str(a.get("land") or "").strip()
        if land and land.lower() not in ("deutschland", "germany"):
            ort = f"{ort}, {land}" if ort else land
        if ort and ort not in places:
            places.append(ort)
    return " | ".join(places)


class Arbeitsagentur(Provider):
    name = "arbeitsagentur"
    wave = "W5"
    kind = "board"
    tenant = False
    hosts = ("rest.arbeitsagentur.de", "www.arbeitsagentur.de")

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        kws = target.options.get("keywords") or [k for k in (target.query or "").split(",") if k.strip()]
        if isinstance(kws, str):
            kws = [kws]
        if not kws:
            raise ProviderError("arbeitsagentur needs keywords (target.query or options.keywords)")
        wo = target.location or target.options.get("wo") or ""
        size = min(int(target.options.get("size") or 100), 100)
        days = int(target.options.get("days") or 30)
        seen: dict[str, Job] = {}
        for kw in kws:
            params = {"was": kw.strip(), "size": size, "page": 1, "angebotsart": 1, "veroeffentlichtseit": days}
            if wo:
                params.update({"wo": wo, "umkreis": int(target.options.get("umkreis") or 50)})
            data = ctx.http.get_json(f"{API}?{urlencode(params)}",
                                     headers={"X-API-Key": API_KEY, "Accept": "application/json"})
            for r in (data or {}).get("ergebnisliste") or []:
                ref = str(r.get("referenznummer") or "")
                title = str(r.get("stellenangebotsTitel") or "").strip()
                if not ref or not title or ref in seen:
                    continue
                loc = _location(r.get("stellenlokationen"))
                seen[ref] = self.job(
                    title=title,
                    url=DETAIL + quote(ref, safe="").replace("%2F", "%252F"),
                    company=str(r.get("firma") or "").strip(),
                    location=loc, country="DE",
                    workplace="remote" if float(r.get("homeofficeprozent") or 0) >= 100 else "",
                    source_id=ref,
                ).validate()
                if len(seen) >= ctx.max_jobs:
                    return list(seen.values())
        return list(seen.values())


PROVIDER = Arbeitsagentur()
