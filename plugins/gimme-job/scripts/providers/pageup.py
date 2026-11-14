"""PageUp — careers.pageuppeople.com/<tenant>/<site>/<lang>/listing/ HTML table (search-results-content).

Mechanism from career-ops providers/pageup.mjs (MIT); list pages only.
"""
from __future__ import annotations

import html
import re
from urllib.parse import urlsplit

from ._base import Context, Job, Provider, ProviderError, Target
from ._parse import html_to_text

ORIGIN = "https://careers.pageuppeople.com"
PAGE_SIZE = 100
MAX_PAGES = 20
TENANT_RE = re.compile(r"^/(\d+)/([A-Za-z0-9_-]+)/([A-Za-z]{2,3}(?:-[A-Za-z0-9]{1,8})?)(?:/|$)")


def _cfg(url: str):
    p = urlsplit(url or "")
    if f"{p.scheme}://{p.netloc}" != ORIGIN:
        return None
    m = TENANT_RE.match(p.path)
    return {"tenant": m.group(1), "site": m.group(2), "lang": m.group(3)} if m else None


def parse_listing(page: str, cfg: dict) -> tuple[list[dict], int, bool]:
    m = re.search(r"""<tbody\b[^<>]*\bid=["']search-results-content["'][^<>]*>""", page, re.I)
    if not m:
        raise ProviderError("pageup: no search-results table (login/challenge page?)")
    end = re.search(r"</tbody\s*>", page[m.end():], re.I)
    body = re.sub(r"<!--.*?-->", "", page[m.end(): m.end() + end.start()] if end else page[m.end():], flags=re.S)
    tail = page[m.end() + end.end():] if end else ""
    jobs, links = [], 0
    for a in re.finditer(r"<a\b([^<>]*)>(.*?)</a\s*>", body, re.S | re.I):
        attrs = a.group(1)
        cls = re.search(r"""\bclass=["']([^"']*)["']""", attrs)
        if not cls or "job-link" not in cls.group(1).split():
            continue
        links += 1
        href = re.search(r"""\bhref=["']([^"']*)["']""", attrs)
        if not href:
            continue
        pm = urlsplit(html.unescape(href.group(1)))
        mm = re.match(r"^/(\d+)/([A-Za-z0-9_-]+)/[^/]+/job/(\d+)(?:/|$)", pm.path)
        if not mm or mm.group(1) != cfg["tenant"] or mm.group(2) != cfg["site"] or (pm.netloc and f"{pm.scheme}://{pm.netloc}" != ORIGIN):
            continue
        title = " ".join(html_to_text(a.group(2)).split())
        if title:
            jobs.append({"id": mm.group(3), "title": title,
                         "url": f"{ORIGIN}/{cfg['tenant']}/{cfg['site']}/{cfg['lang']}/job/{mm.group(3)}"})
    has_more = bool(re.search(r"""<a\b[^<>]*class=["'][^"']*\bmore-link\b""", re.sub(r"<!--.*?-->", "", tail, flags=re.S)))
    return jobs, links, has_more


class PageUp(Provider):
    name = "pageup"
    wave = "W2"
    kind = "ats"
    tenant = True
    hosts = ("careers.pageuppeople.com",)

    def detect(self, careers_url: str):
        c = _cfg(careers_url)
        if not c:
            return None
        return Target(slug=f"{c['tenant']}/{c['site']}", careers_url=careers_url,
                      api_url=f"{ORIGIN}/{c['tenant']}/{c['site']}/{c['lang']}/listing/")

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        c = _cfg(target.api_url) or _cfg(target.careers_url)
        if not c:
            raise ProviderError("pageup needs a careers.pageuppeople.com/<tenant>/<site>/<lang>/ url")
        company = target.company or c["site"]
        jobs: list[Job] = []
        seen: set[str] = set()
        for page in range(1, MAX_PAGES + 1):
            text = ctx.http.get_text(f"{ORIGIN}/{c['tenant']}/{c['site']}/{c['lang']}/listing/?page={page}&page-items={PAGE_SIZE}")
            rows, links, more = parse_listing(text, c)
            fresh = 0
            for r in rows:
                if r["url"] in seen:
                    continue
                seen.add(r["url"])
                fresh += 1
                jobs.append(self.job(title=r["title"], url=r["url"], company=company, source_id=r["id"]).validate())
                if len(jobs) >= ctx.max_jobs:
                    return jobs
            if not fresh or (not more and links < PAGE_SIZE):
                break
        return jobs


PROVIDER = PageUp()
