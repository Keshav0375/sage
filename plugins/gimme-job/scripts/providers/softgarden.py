"""Softgarden — jobs widget HTML at https://<tenant>.softgarden.io/<lang>/widgets/jobs.

Mechanism from career-ops providers/softgarden.mjs (MIT); code is our own.
"""
from __future__ import annotations

import html as htmllib
import re
from datetime import date
from urllib.parse import urljoin, urlsplit

from ._base import Context, Job, Provider, ProviderError, Target


def _widget(url: str) -> str:
    p = urlsplit((url or "").strip())
    host = (p.netloc or "").lower()
    if p.scheme not in ("http", "https") or not (host == "softgarden.io" or host.endswith(".softgarden.io")):
        return ""
    origin = f"{p.scheme}://{p.netloc}"
    if re.search(r"/widgets/jobs/?$", p.path):
        return origin + p.path.rstrip("/")
    m = re.match(r"^/([a-z]{2})(/|$)", p.path)
    return f"{origin}/{m.group(1) if m else 'de'}/widgets/jobs"


def _clean(s: str) -> str:
    return re.sub(r"\s+", " ", htmllib.unescape(re.sub(r"<[^>]*>", " ", s))).strip()


def _date(raw: str) -> str:
    s = raw.strip()
    m = re.fullmatch(r"(\d{1,2})/(\d{1,2})/(\d{2,4})", s)
    if m:
        mo, d, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
    else:
        m = re.fullmatch(r"(\d{1,2})\.(\d{1,2})\.(\d{2,4})", s)
        if not m:
            return ""
        d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
    y = y + 2000 if y < 100 else y
    try:
        return date(y, mo, d).isoformat()
    except ValueError:
        return ""


class Softgarden(Provider):
    name = "softgarden"
    wave = "W4"
    kind = "ats"
    tenant = True
    hosts = ("softgarden.io",)

    def detect(self, careers_url: str):
        w = _widget(careers_url)
        if not w:
            return None
        return Target(slug=urlsplit(w).hostname.split(".")[0], careers_url=careers_url, api_url=w)

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        w = _widget(target.api_url) or _widget(target.careers_url)
        if not w:
            raise ProviderError("softgarden needs a *.softgarden.io url")
        html = ctx.http.get_text(w, headers={"Accept": "text/html"})
        company = target.company or urlsplit(w).hostname.split(".")[0]
        jobs: list[Job] = []
        seen: set[str] = set()
        for block in html.split('<div class="matchElement" id="job_id_')[1:]:
            idm = re.match(r'(\d+)"', block)
            lm = re.search(r'<a href="([^"]*/job/[^"]+)"[^>]*>([\s\S]*?)</a>', block)
            if not idm or not lm or idm.group(1) in seen:
                continue
            title = _clean(lm.group(2))
            if not title:
                continue
            seen.add(idm.group(1))
            cities: list[str] = []
            for cm in re.finditer(r'class="location-view-item"[^>]*>([\s\S]*?)</span>', block):
                c = _clean(cm.group(1))
                if c and c not in cities:
                    cities.append(c)
            dm = re.search(r'class="matchValue date"[^>]*>([\s\S]*?)</div>', block)
            jobs.append(self.job(
                title=title, url=urljoin(w, htmllib.unescape(lm.group(1))), company=company,
                location=" / ".join(cities), posted_at=_date(_clean(dm.group(1))) if dm else "",
                source_id=idm.group(1),
            ).validate())
            if len(jobs) >= ctx.max_jobs:
                break
        return jobs


PROVIDER = Softgarden()
