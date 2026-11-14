"""ALDI Nord group career sites — POST /api/job/hr/query on each country host.

Mechanism from career-ops providers/aldi-nord.mjs (MIT); code is our own.
The API is cumulative: ``page=N`` returns the first N*10 rows, so we ask page 1, then the covering page.
"""
from __future__ import annotations

from urllib.parse import quote, urlsplit

from ._base import Context, Job, Provider, ProviderError, Target
from ._parse import to_iso

SITES = {
    "www.aldi-nord.de": {"de-DE": "/karriere/detail/"},
    "www.aldi.nl": {"nl-NL": "/carriere/detail/"},
    "www.aldi.be": {"nl-BE": "/jobs/detail/", "fr-BE": "/fr/jobs/detail/"},
    "www.aldi.lu": {"fr-LU": "/jobs/detail/"},
    "www.aldi.fr": {"fr-FR": "/carriere/detail/"},
    "www.aldi.es": {"es-ES": "/empleo/detail/"},
    "www.aldi.pt": {"pt-PT": "/carreira/detail/"},
    "www.aldi.pl": {"pl-PL": "/praca/detail/"},
}
PAGE_SIZE = 10


def _host(url: str) -> str:
    h = urlsplit(url or "").netloc.lower()
    if h and not h.startswith("www."):
        h = "www." + h
    return h if h in SITES else ""


def _location(locations) -> str:
    places = []
    for l in locations or []:
        city = " ".join(str(l.get("city") or "").split())
        country = " ".join(str(l.get("country") or "").split())
        if (city or country) and (city, country) not in places:
            places.append((city, country))
    countries = sorted({c for _, c in places if c})
    if len(countries) <= 1:
        cities = list(dict.fromkeys(c for c, _ in places if c))
        return ", ".join(x for x in [" / ".join(cities), countries[0] if countries else ""] if x)
    return "; ".join(", ".join(x for x in p if x) for p in places)


class AldiNord(Provider):
    name = "aldi-nord"
    wave = "W6"
    kind = "company"
    tenant = False
    hosts = tuple(SITES)

    def detect(self, careers_url: str):
        return Target(careers_url=careers_url) if _host(careers_url) else None

    def _rows(self, ctx, host, locale, cats, page):
        data = ctx.http.post_json(f"https://{host}/api/job/hr/query", {
            "careerLevelIds": [], "jobTypeParams": {"jobTypeIds": []}, "jobCategoryIds": cats,
            "title": "", "location": {"searchPhrase": ""}, "page": page, "locale": locale})
        if not isinstance(data, dict) or not isinstance(data.get("results"), list):
            raise ProviderError("aldi-nord: unexpected response")
        return data

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        host = _host(target.careers_url) or _host(str(target.options.get("host", ""))) or "www.aldi-nord.de"
        locales = target.options.get("locales") or list(SITES[host])
        cats = [str(c) for c in target.options.get("categories") or []]
        company = target.company or "ALDI Nord"
        jobs: list[Job] = []
        seen: set[str] = set()
        for locale in locales:
            if locale not in SITES[host]:
                continue
            data = self._rows(ctx, host, locale, cats, 1)
            if data.get("hasNextPage"):
                total = data.get("total") if isinstance(data.get("total"), int) else 0
                nxt = max(2, -(-total // PAGE_SIZE)) if total else 2
                nxt = min(nxt, max(2, -(-ctx.max_jobs // PAGE_SIZE)))
                try:
                    more = self._rows(ctx, host, locale, cats, nxt)
                    if len(more["results"]) > len(data["results"]):
                        data = more
                except ProviderError:
                    ctx.warn("aldi-nord: kept first page only")
            for row in data["results"]:
                title = " ".join(str(row.get("title") or "").split())
                slug, pid = str(row.get("slugTitle") or "").strip(), str(row.get("postingId") or "").strip()
                if not (title and slug and pid):
                    continue
                url = f"https://{host}{SITES[host][locale]}{quote(slug)}-{quote(pid)}.html"
                if url in seen:
                    continue
                seen.add(url)
                jobs.append(self.job(title=title, url=url, company=company,
                                     location=_location(row.get("locations")),
                                     posted_at=to_iso(row.get("onlineFrom")),
                                     source_id=pid, extra={"language": locale}).validate())
                if len(jobs) >= ctx.max_jobs:
                    return jobs
        return jobs


PROVIDER = AldiNord()
