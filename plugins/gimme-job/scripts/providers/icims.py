"""iCIMS — public hosted-portal search pages (HTML scrape).

GET https://careers-<tenant>.icims.com/jobs/search?ss=1&pr=<page>&in_iframe=1
List pages carry title/location/url only (no dates). Mechanism from career-ops providers/icims.mjs (MIT).
"""
from __future__ import annotations

import html
import re
from urllib.parse import urljoin, urlsplit

from ._base import Context, Job, Provider, ProviderError, Target

MAX_PAGES = 30
BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html",
}
_HREF = re.compile(r'href="([^"]*/jobs/\d+/[^"/]+/job[^"]*)"')
_TITLE = re.compile(r"<h3\b[^>]*>\s*(.*?)</h3>", re.S)
_LOC = re.compile(
    r"""<span\b[^>]*class=["'][^"']*(?<![\w-])field-label(?![\w-])[^"']*["'][^>]*>\s*Location\b[^<]*</span>\s*<span\b[^>]*>\s*(.*?)</span>""",
    re.S)


def _origin(url: str) -> str:
    p = urlsplit(url or "")
    if p.scheme != "https" or not p.netloc.lower().endswith(".icims.com"):
        return ""
    return f"https://{p.netloc.lower()}"


def _clean(s: str) -> str:
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", s)).split())


def parse_search_page(page: str, origin: str) -> list[dict]:
    out = []
    for card in page.split("iCIMS_JobCardItem")[1:]:
        h = _HREF.search(card)
        if not h:
            continue
        full = urljoin(origin + "/", html.unescape(h.group(1)))
        sp = urlsplit(full)
        if f"{sp.scheme}://{sp.netloc}" != origin:
            continue
        t = _TITLE.search(card)
        if not t or not _clean(t.group(1)):
            continue
        loc = _LOC.search(card)
        m = re.search(r"/jobs/(\d+)/", sp.path)
        out.append({"title": _clean(t.group(1)), "url": f"{origin}{sp.path}",
                    "location": _clean(loc.group(1)) if loc else "", "id": m.group(1) if m else ""})
    return out


class Icims(Provider):
    name = "icims"
    wave = "W2"
    kind = "ats"
    tenant = True
    hosts = ("icims.com",)

    def detect(self, careers_url: str):
        origin = _origin(careers_url)
        if not origin:
            return None
        return Target(careers_url=careers_url, slug=urlsplit(origin).netloc.split(".")[0],
                      api_url=f"{origin}/jobs/search?ss=1&in_iframe=1")

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        origin = _origin(target.api_url) or _origin(target.careers_url)
        if not origin:
            raise ProviderError("icims needs an https *.icims.com careers url")
        jobs: list[Job] = []
        prev_first = None
        for page in range(MAX_PAGES):
            text = ctx.http.get_text(f"{origin}/jobs/search?ss=1&pr={page}&in_iframe=1", headers=BROWSER_HEADERS)
            rows = parse_search_page(text, origin)
            if not rows or rows[0]["url"] == prev_first:
                break
            prev_first = rows[0]["url"]
            for r in rows:
                jobs.append(self.job(title=r["title"], url=r["url"], company=target.company or target.slug,
                                     location=r["location"], source_id=r["id"]).validate())
                if len(jobs) >= ctx.max_jobs:
                    return jobs
        return jobs


PROVIDER = Icims()
