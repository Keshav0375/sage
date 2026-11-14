"""Apple Jobs — server-rendered search page with a hydration blob (no auth).

GET https://jobs.apple.com/en-us/search?search=..&location=..&page=N
window.__staticRouterHydrationData = JSON.parse("...") -> loaderData.search.{searchResults[], totalRecords}
Needs a query (target.query / options['queries']) or options['teams']; there is no default search.
Mechanism from career-ops providers/apple.mjs (MIT); code is our own.
"""
from __future__ import annotations

import json
import re
from urllib.parse import quote, urlencode, urlsplit

from ._base import Context, Job, Provider, ProviderError, Target
from ._parse import to_iso

BASE = "https://jobs.apple.com"
PAGE_SIZE = 20
HYDRATION = re.compile(r'window\.__staticRouterHydrationData\s*=\s*JSON\.parse\("((?:\\.|[^"\\])*)"\)')


def parse_hydration(html: str):
    m = HYDRATION.search(html or "")
    if not m:
        return None
    try:
        data = json.loads(json.loads(f'"{m.group(1)}"'))
        return ((data.get("loaderData") or {}).get("search")) or None
    except ValueError:
        return None


def _place(l: dict) -> str:
    name, country = l.get("name"), l.get("countryName")
    if not isinstance(name, str) or not isinstance(country, str):
        return name if isinstance(name, str) else ""
    return f"{name}, {country}" if name and country and l.get("level") != 1 and country not in name else name


class Apple(Provider):
    name = "apple"
    wave = "W3"
    kind = "company"
    tenant = False
    hosts = ("jobs.apple.com",)

    def detect(self, careers_url: str):
        if urlsplit(careers_url or "").netloc.lower() == "jobs.apple.com":
            return Target(company="Apple", careers_url=careers_url)
        return None

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        o = target.options
        loc = o.get("location") or target.location or "united-states-USA"

        def lst(v):
            return [str(x).strip() for x in v if str(x).strip()] if isinstance(v, list) else []
        queries = lst(o.get("queries")) or ([target.query] if target.query else [])
        teams = lst(o.get("teams"))
        if not queries and not teams:
            raise ProviderError("apple needs a query (target.query / options.queries) or options.teams")
        max_pages = min(int(o.get("max_pages") or 2), 50)
        axes = [{"search": q, "location": loc, "sort": "relevance"} for q in queries] + \
               [{"location": loc, "team": t} for t in teams]
        by_url: dict[str, Job] = {}
        for base in axes:
            for page in range(1, max_pages + 1):
                url = f"{BASE}/en-us/search?{urlencode({**base, 'page': page})}"
                search = parse_hydration(ctx.http.get_text(url))
                if search is None:
                    raise ProviderError(f"apple: no hydration blob in {url}")
                rows = search.get("searchResults")
                if not isinstance(rows, list):
                    raise ProviderError("apple: searchResults missing or not a list")
                for r in rows:
                    if not r.get("postingTitle") or not r.get("id"):
                        continue
                    team = (r.get("team") or {}).get("teamCode")
                    j_url = f"{BASE}/en-us/details/{quote(str(r['id']), safe='')}/{quote(str(r.get('transformedPostingTitle') or 'role'), safe='')}"
                    if team:
                        j_url += f"?team={quote(str(team), safe='')}"
                    names = list(dict.fromkeys(p for p in (_place(l) for l in (r.get("locations") or []) if isinstance(l, dict)) if p))
                    if not names and r.get("isMultiLocation"):
                        names = ["Various Locations within United States"]
                    if j_url in by_url:
                        continue
                    by_url[j_url] = self.job(
                        title=str(r["postingTitle"]).strip(), url=j_url, company="Apple",
                        location="; ".join(names), locations=names,
                        posted_at=to_iso(r.get("postDateInGMT")),
                        department=(r.get("team") or {}).get("teamName", "") or "",
                        source_id=str(r["id"]),
                        extra={"pipeline": True} if r.get("type") == "PIPE" else {},
                    ).validate()
                    if len(by_url) >= ctx.max_jobs:
                        return list(by_url.values())
                total = int(search.get("totalRecords") or 0)
                if len(rows) < PAGE_SIZE or page * PAGE_SIZE >= total:
                    break
        return list(by_url.values())


PROVIDER = Apple()
