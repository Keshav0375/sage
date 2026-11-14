"""NEOGOV (governmentjobs.com / schooljobs.com) — HTML list /careers/home/index?agency=<agency>&page=N.

Mechanism from career-ops providers/neogov.mjs (MIT); code is our own.
"""
from __future__ import annotations

import html as htmllib
import re
from urllib.parse import urlencode, urljoin, urlsplit

from ._base import Context, Job, Provider, ProviderError, Target

ORIGINS = {
    "schooljobs.com": "https://www.schooljobs.com", "www.schooljobs.com": "https://www.schooljobs.com",
    "governmentjobs.com": "https://www.governmentjobs.com", "www.governmentjobs.com": "https://www.governmentjobs.com",
}
SEG = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$", re.I)
MAX_PAGES = 30


def _target(url: str):
    p = urlsplit((url or "").strip())
    origin = ORIGINS.get((p.hostname or "").lower())
    if p.scheme != "https" or not origin:
        return None
    parts = [x for x in p.path.split("/") if x]
    if len(parts) < 2 or parts[0] != "careers" or not SEG.match(parts[1]) or parts[1].lower() == "home":
        return None
    folder = parts[2] if len(parts) > 2 else ""
    if folder and not SEG.match(folder):
        return None
    return origin, parts[1].lower(), folder.lower()


def _page_url(t, page: int) -> str:
    q = {"agency": t[1]}
    if t[2]:
        q["departmentFolder"] = t[2]
    q.update({"sort": "PostingDate", "isDescendingSort": "true", "page": page})
    return f"{t[0]}/careers/home/index?{urlencode(q)}"


def _text(s: str) -> str:
    return re.sub(r"\s+", " ", htmllib.unescape(re.sub(r"<[^>]+>", " ", s or ""))).strip()


class Neogov(Provider):
    name = "neogov"
    wave = "W4"
    kind = "ats"
    tenant = True
    hosts = ("governmentjobs.com", "schooljobs.com")

    def detect(self, careers_url: str):
        t = _target(careers_url)
        return Target(slug=t[1], careers_url=careers_url, api_url=_page_url(t, 1)) if t else None

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        t = _target(target.careers_url) or _target(target.api_url)
        if not t:
            raise ProviderError("neogov needs https://www.schooljobs.com/careers/<agency>[/<folder>] or governmentjobs.com")
        origin = t[0]
        company = target.company or t[1]
        jobs: list[Job] = []
        seen: set[str] = set()
        for page in range(1, MAX_PAGES + 1):
            html = ctx.http.get_text(_page_url(t, page), headers={"X-Requested-With": "XMLHttpRequest"})
            if not html.strip():
                break
            items = re.split(r'<li class="list-item"', html, flags=re.I)[1:]
            if not items:
                if "jobs-not-found-container" in html or "search-results-listing-container" in html:
                    break
                raise ProviderError("neogov: response is not a NEOGOV job list")
            fresh = 0
            for item in items:
                lm = (re.search(r'<a [^>]*class="item-details-link"[^>]*href="([^"]+)"[^>]*>([\s\S]*?)</a>', item, re.I)
                      or re.search(r'<a [^>]*href="([^"]+)"[^>]*class="item-details-link"[^>]*>([\s\S]*?)</a>', item, re.I))
                if not lm:
                    continue
                u = urlsplit(urljoin(origin, htmllib.unescape(lm.group(1))))
                title = _text(lm.group(2))
                if f"{u.scheme}://{u.netloc}" != origin or not re.match(r"^/careers/[^/]+/(?:[^/]+/)?jobs/\d+", u.path) or not title:
                    continue
                url = f"{origin}{u.path}" + (f"?{u.query}" if u.query else "")
                if url in seen:
                    continue
                seen.add(url)
                fresh += 1
                meta = re.search(r'<ul class="list-meta">([\s\S]*?)</ul>', item, re.I)
                first = re.search(r"<li>([\s\S]*?)</li>", meta.group(1), re.I) if meta else None
                jid = re.search(r"/jobs/(\d+)", u.path)
                jobs.append(self.job(title=title, url=url, company=company,
                                     location=_text(first.group(1)) if first else "",
                                     source_id=jid.group(1) if jid else "").validate())
                if len(jobs) >= ctx.max_jobs:
                    return jobs
            if fresh == 0:
                break
        return jobs


PROVIDER = Neogov()
