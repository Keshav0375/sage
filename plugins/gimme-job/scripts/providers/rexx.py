"""rexx systems — employer-branded job list page (stellenangebote.html), paginated with ?start=N.

Mechanism from career-ops providers/rexx.mjs (MIT); code is our own.
Branded domains cannot be auto-detected, so detect() returns None; give careers_url explicitly.
Simplified: no Atom-feed date join.
"""
from __future__ import annotations

import html as htmllib
import re
from urllib.parse import urljoin, urlsplit

from ._base import Context, Job, Provider, ProviderError, Target

DEFAULT_PAGE = "stellenangebote.html"
MAX_PAGES = 30
CARD = re.compile(r"""<(?:article|div)\b[^>]*\bclass=["'][^"']*\bjoboffer_container\b[^"']*["'][^>]*>""", re.I)
ANCHOR = re.compile(r"""<a\b[^>]*\bhref=["']([^"']+)["'][^>]*>([\s\S]*?)</a>""", re.I)
DETAIL = re.compile(r"-j(\d+)\.html$", re.I)
STANDORT = re.compile(r"""<span\b[^>]*\bclass=["'][^"']*\bjob_standort\b[^"']*["'][^>]*>([\s\S]*?)</span>""", re.I)
INFO = re.compile(r"""<div\b[^>]*\bclass=["'][^"']*\bjoboffer_informations\b[^"']*["'][^>]*>([^<]*)</div>""", re.I)


def _public_host(host: str) -> bool:
    if not host or "." not in host or host.startswith("["):
        return False
    if re.fullmatch(r"\d+(?:\.\d+){0,3}", host) or re.fullmatch(r"0x[0-9a-f]+", host, re.I):
        return False
    return not re.search(r"(^|\.)(localhost|local|internal|localdomain|home\.arpa|lan)$", host)


def _list_url(url: str):
    p = urlsplit((url or "").strip())
    host = (p.hostname or "").lower().rstrip(".")
    if p.scheme != "https" or not _public_host(host):
        return None
    path = p.path or "/"
    if path.endswith("/"):
        path += DEFAULT_PAGE
    return host, f"https://{host}{path}"


def _text(h: str) -> str:
    return re.sub(r"\s+", " ", htmllib.unescape(re.sub(r"<[^>]*>", " ", h))).strip()


class Rexx(Provider):
    name = "rexx"
    wave = "W4"
    kind = "ats"
    tenant = True
    hosts = ()

    def detect(self, careers_url: str):
        return None  # branded domains: configure careers_url on the target explicitly

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        r = _list_url(target.api_url or target.careers_url)
        if not r:
            raise ProviderError("rexx needs an https careers_url pointing at the rexx job list page")
        host, list_url = r
        company = target.company or host
        jobs: list[Job] = []
        seen: set[str] = set()
        offset = page_size = 0
        for page in range(MAX_PAGES):
            url = list_url if offset == 0 else f"{list_url}?start={offset}"
            html = ctx.http.get_text(url)
            starts = [m.start() for m in CARD.finditer(html)]
            fresh = 0
            for i, s in enumerate(starts):
                card = html[s: starts[i + 1] if i + 1 < len(starts) else None]
                link = title = None
                for a in ANCHOR.finditer(card):
                    u = urlsplit(urljoin(url, htmllib.unescape(a.group(1)).strip()))
                    m = DETAIL.search(u.path)
                    if u.scheme == "https" and (u.hostname or "").lower() == host and m:
                        link, title = (m.group(1), f"https://{host}{u.path}" + (f"?{u.query}" if u.query else "")), _text(a.group(2))
                        break
                if not link or not title or link[0] in seen:
                    continue
                seen.add(link[0])
                fresh += 1
                sm = STANDORT.search(card)
                loc = _text(sm.group(1)) if sm else ""
                if not loc:
                    boxes = [_text(b) for b in INFO.findall(card) if _text(b)]
                    loc = boxes[-1] if boxes else ""
                jobs.append(self.job(title=title, url=link[1], company=company, location=loc,
                                     source_id=link[0]).validate())
                if len(jobs) >= ctx.max_jobs:
                    return jobs
            if page == 0:
                if not starts:
                    if re.search(r"href=[\"'][^\"']*-j\d+\.html", html, re.I):
                        raise ProviderError("rexx: page contains postings but none could be parsed")
                    if not re.search(r"""\bid=["']joboffers["']""", html, re.I):
                        raise ProviderError("rexx: not a rexx job list (no #joboffers container)")
                page_size = len(starts)
            offset += len(starts)
            if not starts or len(starts) < page_size or fresh == 0:
                break
        return jobs


PROVIDER = Rexx()
