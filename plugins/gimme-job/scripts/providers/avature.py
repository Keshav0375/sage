"""Avature career sites — HTML SearchJobs listing, 6 results per page (offset via jobOffset, fallback offset).

Mechanism from career-ops providers/avature.mjs (MIT).
"""
from __future__ import annotations

import html
import re
from datetime import date
from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit

from ._base import Context, Job, Provider, ProviderError, Target

PAGE_SIZE = 6
MAX_PAGES = 50
MONTHS = {m: i + 1 for i, m in enumerate("jan feb mar apr may jun jul aug sep oct nov dec".split())}
ARTICLE = re.compile(r'<article class="(?:article )?article--(?:result|jobs)\b[^"]*".*?</article>', re.S)
TITLE_RES = [
    re.compile(r'article__header__text__title[^>]*>\s*<a[^>]*href="([^"]*/JobDetail[/?][^"]+)"[^>]*>(.*?)</a>', re.S),
    re.compile(r'<a[^>]*class="link"[^>]*href="([^"]*/JobDetail[/?][^"]+)"[^>]*>(.*?)</a>', re.S),
    re.compile(r'<a[^>]*href="([^"]*/JobDetail[/?][^"]+)"[^>]*>(.*?)</a>', re.S),
]
LOC_RES = [re.compile(p, re.S | re.I) for p in (r"list-item-location[^>]*>(.*?)</span>",
                                                r'class="[^"]*\blocation\b[^"]*"[^>]*>(.*?)</(?:span|div|li)>')]


def _clean(s: str) -> str:
    return " ".join(html.unescape(re.sub(r"<[^>]*>", " ", s)).split())


def parse_articles(page: str, origin: str) -> list[dict]:
    out = []
    for a in ARTICLE.finditer(page):
        block = a.group(0)
        m = next((r.search(block) for r in TITLE_RES if r.search(block)), None)
        if not m or not _clean(m.group(2)):
            continue
        url = urljoin(origin + "/", html.unescape(m.group(1)))
        idm = re.search(r"/JobDetail/[^/]*/(\d+)", url) or re.search(r"[?&]jobId=(\d+)", url, re.I)
        loc = next((r.search(block) for r in LOC_RES if r.search(block)), None)
        pm = re.search(r"Posted\s+(\d{1,2})-([A-Za-z]{3})-(\d{4})", block)
        posted = ""
        if pm and pm.group(2).lower() in MONTHS:
            try:
                posted = date(int(pm.group(3)), MONTHS[pm.group(2).lower()], int(pm.group(1))).isoformat()
            except ValueError:
                pass
        out.append({"id": idm.group(1) if idm else url, "title": _clean(m.group(2)), "url": url,
                    "location": _clean(loc.group(1)) if loc else "", "posted": posted})
    return out


class Avature(Provider):
    name = "avature"
    wave = "W2"
    kind = "ats"
    tenant = True
    hosts = ("avature.net",)

    def detect(self, careers_url: str):
        host = urlsplit(careers_url or "").netloc.lower()
        if host == "avature.net" or host.endswith(".avature.net"):
            return Target(slug=host.split(".")[0], careers_url=careers_url, api_url=careers_url)
        return None

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        raw = target.api_url or target.careers_url
        u = urlsplit(raw or "")
        if u.scheme not in ("http", "https") or not u.netloc:
            raise ProviderError("avature needs a careers url")
        origin = f"{u.scheme}://{u.netloc}"
        path = u.path.rstrip("/") if re.search(r"/SearchJobs\b", u.path, re.I) else "/careers/SearchJobs"
        extra = [(k, v) for k, v in parse_qsl(u.query) if k.lower() not in ("joboffset", "offset")]
        param = str(target.options.get("offset_param") or "jobOffset")
        can_heal = "offset_param" not in target.options
        company = target.company or u.netloc.split(".")[0]
        jobs: list[Job] = []
        seen: set[str] = set()

        def get(p: str, page: int):
            text = ctx.http.get_text(f"{origin}{path}?{urlencode(extra + [(p, page * PAGE_SIZE)])}", headers={"Accept": "text/html"})
            return parse_articles(text, origin), len(ARTICLE.findall(text))

        def absorb(arts) -> int:
            fresh = 0
            for a in arts:
                if a["id"] in seen:
                    continue
                seen.add(a["id"])
                fresh += 1
                jobs.append(self.job(title=a["title"], url=a["url"], company=company, location=a["location"],
                                     posted_at=a["posted"], source_id=a["id"]).validate())
            return fresh

        for page in range(MAX_PAGES):
            arts, cards = get(param, page)
            fresh = absorb(arts)
            if (cards == 0 or (fresh == 0 and arts)) and can_heal and page == 1:
                can_heal = False
                arts2, cards2 = get("offset", page)
                f2 = absorb(arts2)
                if f2 > 0:
                    param, arts, cards, fresh = "offset", arts2, cards2, f2
            if len(jobs) >= ctx.max_jobs:
                return jobs[: ctx.max_jobs]
            if cards == 0 or (fresh == 0 and arts) or cards < PAGE_SIZE:
                break
        return jobs


PROVIDER = Avature()
