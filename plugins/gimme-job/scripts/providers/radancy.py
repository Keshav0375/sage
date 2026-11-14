"""Radancy / TalentBrew career sites — /<lang>/search-jobs/results JSON fragment (HTML inside), HTML fallback.

Not URL-detectable (branded domains); pass careers_url. Mechanism from career-ops providers/radancy.mjs (MIT).
"""
from __future__ import annotations

import html
import re
import uuid
from urllib.parse import urlencode, urljoin, urlsplit

from ._base import Context, Job, Provider, ProviderError, Target

MAX_PAGES = 200
PER_PAGE = 100


def _clean(s: str) -> str:
    return " ".join(html.unescape(re.sub(r"<[^>]*>", " ", s)).split())


def _list_url(raw: str) -> str:
    u = urlsplit(raw or "")
    if u.scheme not in ("http", "https") or not u.netloc:
        return ""
    if re.search(r"/search-jobs/?$", u.path):
        return f"{u.scheme}://{u.netloc}{u.path.rstrip('/')}"
    m = re.match(r"^/([a-z]{2})(/|$)", u.path)
    return f"{u.scheme}://{u.netloc}/{m.group(1) if m else 'en'}/search-jobs"


def parse_results(text: str, origin: str) -> list[dict]:
    out, seen = [], set()
    for block in re.split(r'<li class="search-results-list__item', text or "")[1:]:
        link = re.search(r'search-results-list__job-link[^"]*"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', block, re.S)
        if not link:
            continue
        href = html.unescape(link.group(1))
        did = re.search(r'data-job-id="([^"]+)"', block)
        ids = re.findall(r"/(\d+)(?=[/?#]|$)", href)
        jid = did.group(1) if did else (ids[-1] if ids else href)
        title = _clean(link.group(2))
        if jid in seen or not title:
            continue
        seen.add(jid)
        loc = re.search(r"__job-info--location.*?<span>(.*?)</span>", block, re.S)
        out.append({"id": jid, "title": title, "url": urljoin(origin + "/", href), "location": _clean(loc.group(1)) if loc else ""})
    if out:
        return out
    anchors = list(re.finditer(r"<a\b([^>]*)>(.*?)</a>", text or "", re.S | re.I))
    for n, a in enumerate(anchors):
        attrs, inner = a.group(1), a.group(2)
        did, href = re.search(r'data-job-id="([^"]+)"', attrs, re.I), re.search(r'href="([^"]+)"', attrs, re.I)
        if not did or not href or "/job/" not in html.unescape(href.group(1)) or did.group(1) in seen:
            continue
        head = re.search(r"<h[1-6][^>]*>(.*?)</h[1-6]>", inner, re.S | re.I)
        title = _clean(head.group(1) if head else re.sub(r"<span.*?</span>", " ", inner, flags=re.S | re.I))
        if not title:
            continue
        end = anchors[n + 1].start() if n + 1 < len(anchors) else len(text)
        loc = re.search(r"""class="(?:[^"]*\bjob-location\b[^"]*|(?:[^"]*\s)?location(?:\s[^"]*)?)"[^>]*>(.*?)</(?:span|p|div)>""",
                        inner + text[a.end():end], re.S | re.I)
        seen.add(did.group(1))
        out.append({"id": did.group(1), "title": title, "url": urljoin(origin + "/", html.unescape(href.group(1))),
                    "location": _clean(loc.group(1)) if loc else ""})
    return out


class Radancy(Provider):
    name = "radancy"
    wave = "W2"
    kind = "ats"
    tenant = True
    hosts = ()

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        base = _list_url(target.api_url or target.careers_url)
        if not base:
            raise ProviderError("radancy needs a careers_url")
        u = urlsplit(base)
        origin = f"{u.scheme}://{u.netloc}"
        company = target.company or u.netloc.split(".")[-2 if u.netloc.count(".") else 0]
        jobs: list[Job] = []
        seen: set[str] = set()

        def add(rows) -> int:
            fresh = 0
            for r in rows:
                if r["id"] in seen:
                    continue
                seen.add(r["id"])
                fresh += 1
                jobs.append(self.job(title=r["title"], url=r["url"], company=company, location=r["location"], source_id=r["id"]).validate())
            return fresh

        def frag(page: int):
            q = urlencode({"ActiveFacetID": 0, "CurrentPage": page, "RecordsPerPage": PER_PAGE, "Distance": 50, "RadiusUnitType": 0,
                           "Keywords": "", "Location": "", "ShowRadius": "False", "IsPagination": "True", "CustomFacetName": "",
                           "FacetTerm": "", "FacetType": 0, "SearchResultsModuleName": "Search Results", "SortCriteria": 0,
                           "SortDirection": 0, "SearchType": 5, "_": uuid.uuid4()})
            data = ctx.http.get_json(f"{base}/results?{q}", headers={"Accept": "application/json", "X-Requested-With": "XMLHttpRequest"})
            if not isinstance(data, dict) or not isinstance(data.get("results"), str):
                raise ProviderError("radancy: unexpected fragment shape")
            return data["results"]

        try:
            first = frag(1)
            rows = parse_results(first, origin)
            if rows:
                tp = re.search(r'data-total-pages="(\d+)"', first)
                last = min(int(tp.group(1)) if tp else MAX_PAGES, MAX_PAGES)
                add(rows)
                for page in range(2, last + 1):
                    if len(jobs) >= ctx.max_jobs:
                        break
                    rows = parse_results(frag(page), origin)
                    if not rows or add(rows) == 0:
                        break
                return jobs[: ctx.max_jobs]
        except ProviderError:
            pass
        for page in range(1, MAX_PAGES + 1):
            rows = parse_results(ctx.http.get_text(f"{base}?p={page}", headers={"Accept": "text/html"}), origin)
            if not rows or add(rows) == 0 or len(jobs) >= ctx.max_jobs:
                break
        return jobs[: ctx.max_jobs]


PROVIDER = Radancy()
