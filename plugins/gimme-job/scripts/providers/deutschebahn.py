"""Deutsche Bahn — db.jobs server-rendered search results (HTML fragment).

Mechanism from career-ops providers/deutschebahn.mjs (MIT); code is our own.
"""
from __future__ import annotations

import html
import re
from urllib.parse import urljoin, urlsplit

from ._base import Context, Job, Provider, Target

ITEMS = 1000
MAX_PAGES = 5
DEFAULT_ID = "5441588"
HIT_RE = re.compile(r'<a\b[^>]*class="[^"]*m-search-hit\b[^"]*"[^>]*>([\s\S]*?)</a>', re.I)


def _clean(s: str) -> str:
    return " ".join(html.unescape(re.sub(r"<[^>]*>", " ", s)).split())


def _is_db(url: str) -> bool:
    h = urlsplit(url or "").netloc.lower()
    return h == "db.jobs" or h.endswith(".db.jobs")


class DeutscheBahn(Provider):
    name = "deutschebahn"
    wave = "W6"
    kind = "company"
    tenant = False
    hosts = ("db.jobs",)

    def detect(self, careers_url: str):
        return Target(careers_url=careers_url) if _is_db(careers_url) else None

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        raw = target.careers_url or "https://db.jobs/"
        p = urlsplit(raw)
        origin = f"{p.scheme}://{p.netloc}" if _is_db(raw) else "https://db.jobs"
        m = re.search(r"/service/search/de-de/(\d+)", p.path) or re.search(r"/(\d{6,})(?:[/?]|$)", p.path)
        base = f"{origin}/service/search/de-de/{m.group(1) if m else DEFAULT_ID}"
        jobs: list[Job] = []
        seen: set[str] = set()
        for page in range(MAX_PAGES):
            page_html = ctx.http.get_text(
                f"{base}?qli=true&query=&sort=pubExternalDate_tdt&itemsPerPage={ITEMS}&pageNum={page}",
                headers={"Accept": "text/html"})
            anchors = HIT_RE.finditer(page_html)
            n = 0
            for a in anchors:
                n += 1
                href = re.search(r'href="([^"]+)"', a.group(0))
                if not href:
                    continue
                href_v = html.unescape(href.group(1))
                idm = re.search(r'data-job-id="([^"]+)"', a.group(0))
                jid = idm.group(1) if idm else href_v
                tm = re.search(r'm-search-hit__title-text"[^>]*>([\s\S]*?)</span>', a.group(1), re.I)
                title = _clean(tm.group(1)) if tm else ""
                if not title or jid in seen:
                    continue
                lm = re.search(r'aria-label="Arbeitsort"[^>]*></i>([\s\S]*?)</li>', a.group(1), re.I)
                seen.add(jid)
                jobs.append(self.job(title=title, url=urljoin(origin, href_v),
                                     company=target.company or "Deutsche Bahn",
                                     location=_clean(lm.group(1)) if lm else "",
                                     source_id=jid).validate())
                if len(jobs) >= ctx.max_jobs:
                    return jobs
            if n < ITEMS:
                break
        return jobs


PROVIDER = DeutscheBahn()
