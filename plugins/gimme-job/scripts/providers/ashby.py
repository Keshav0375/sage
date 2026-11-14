"""Ashby — public posting API (no auth).

GET https://api.ashbyhq.com/posting-api/job-board/{slug}?includeCompensation=true
Mechanism from career-ops providers/ashby.mjs (MIT); code is our own.
Simplified: skips the jobs.ashbyhq.com embed-page fallback.
"""
from __future__ import annotations

from urllib.parse import urlsplit

from ._base import Context, Job, Provider, ProviderError, Target
from ._parse import employment_from, to_iso, workplace_from

API = "https://api.ashbyhq.com/posting-api/job-board/{slug}?includeCompensation=true"
_PERIOD = {"1 HOUR": "hour", "1 MONTH": "month", "1 YEAR": "year"}
_ANNUALIZE = {"1 DAY": 260, "1 WEEK": 52, "2 WEEK": 26}


def _num(v):
    try:
        n = float(v)
        return n if n >= 0 else None
    except (TypeError, ValueError):
        return None


def _salary(comp) -> dict:
    if not isinstance(comp, dict):
        return {}
    comps = [c for t in comp.get("compensationTiers") or [] for c in t.get("components") or []
             if str(c.get("compensationType", "")).lower() == "salary"]
    best = None
    for c in comps:
        lo, hi = _num(c.get("minValue")), _num(c.get("maxValue"))
        if (lo is None and hi is None) or c.get("interval") not in {**_PERIOD, **_ANNUALIZE}:
            continue
        if best is None:
            best = c
    if best is None:
        return {}
    lo, hi = _num(best.get("minValue")), _num(best.get("maxValue"))
    lo, hi = (lo if lo is not None else hi), (hi if hi is not None else lo)
    iv = best["interval"]
    mult = _ANNUALIZE.get(iv, 1)
    return dict(salary_min=min(lo, hi) * mult, salary_max=max(lo, hi) * mult,
                currency=str(best.get("currencyCode") or "").upper(),
                salary_period=_PERIOD.get(iv, "year"))


class Ashby(Provider):
    name = "ashby"
    wave = "W1"
    kind = "ats"
    tenant = True
    hosts = ("ashbyhq.com",)

    def detect(self, careers_url: str):
        p = urlsplit(careers_url or "")
        if p.netloc.lower() != "jobs.ashbyhq.com":
            return None
        parts = [x for x in p.path.split("/") if x]
        if not parts:
            return None
        return Target(slug=parts[0], careers_url=careers_url, api_url=API.format(slug=parts[0]))

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        slug = target.slug or (self.detect(target.careers_url) or Target()).slug
        if not slug:
            raise ProviderError("ashby needs a board slug")
        data = ctx.http.get_json(target.api_url or API.format(slug=slug))
        if not isinstance(data, dict) or not isinstance(data.get("jobs"), list):
            raise ProviderError("ashby: expected {jobs: [...]}")
        jobs: list[Job] = []
        for j in data["jobs"][: ctx.max_jobs]:
            if j.get("isListed") is False:
                continue
            places = [j.get("location") or ""] + [s.get("location", "") for s in j.get("secondaryLocations") or []]
            places = [p for i, p in enumerate(places) if p and p not in places[:i]]
            wp = workplace_from(j.get("workplaceType")) or ("remote" if j.get("isRemote") else "")
            country = ((j.get("address") or {}).get("postalAddress") or {}).get("addressCountry", "")
            jobs.append(self.job(
                title=j.get("title", ""), url=j.get("jobUrl", ""),
                company=target.company or slug,
                location="; ".join(places), locations=places, country=country, workplace=wp,
                employment=employment_from(j.get("employmentType")),
                department=j.get("department") or j.get("team") or "",
                posted_at=to_iso(j.get("publishedAt")),
                description=j.get("descriptionPlain") or "",
                source_id=str(j.get("id", "")), **_salary(j.get("compensation")),
            ).validate())
        return jobs


PROVIDER = Ashby()
