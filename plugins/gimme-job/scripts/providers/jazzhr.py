"""JazzHR / ApplyToJob — scrape the public board at https://<tenant>.applytojob.com/apply.

Mechanism from career-ops providers/jazzhr.mjs (MIT); list page only (no detail enrichment).
"""
from __future__ import annotations

import html
import re
from urllib.parse import urljoin, urlsplit

from ._base import Context, Job, Provider, ProviderError, Target
from ._parse import html_to_text

HOST_RE = re.compile(r"^[a-z0-9][a-z0-9-]*\.applytojob\.com$", re.I)
LINK = re.compile(r"""<a\b[^>]*href=["']([^"']*/apply/[^"']+)["'][^>]*>(.*?)</a>""", re.S | re.I)


def _origin(url: str) -> str:
    p = urlsplit((url or "").strip())
    host = p.netloc.lower()
    return f"https://{host}" if p.scheme == "https" and HOST_RE.match(host) else ""


def _clean(s: str) -> str:
    return " ".join(html_to_text(s).split())


def parse_list(page: str, board: str) -> list[dict]:
    base = urlsplit(board)
    out: dict[str, dict] = {}

    def add(href: str, title: str, loc: str):
        u = urlsplit(urljoin(board, html.unescape(href)))
        if u.netloc != base.netloc or not re.match(r"^/apply/[^/]", u.path):
            return
        url = f"https://{u.netloc}{u.path}"
        if title and url not in out:
            out[url] = {"title": title, "url": url, "location": loc}

    for card in re.finditer(r"""<li\b[^>]*class=["'][^"']*list-group-item[^"']*["'][^>]*>(.*?)</li>""", page, re.S | re.I):
        c = card.group(1)
        link = LINK.search(c)
        if not link:
            continue
        loc = re.search(r"fa-map-marker[^<]*</i>\s*([^<]+)", c, re.I)
        add(link.group(1), _clean(link.group(2)), _clean(loc.group(1)) if loc else "")
    for m in LINK.finditer(page):
        add(m.group(1), _clean(m.group(2)), "")
    return list(out.values())


class JazzHR(Provider):
    name = "jazzhr"
    wave = "W2"
    kind = "ats"
    tenant = True
    hosts = ("applytojob.com",)

    def detect(self, careers_url: str):
        o = _origin(careers_url)
        if not o:
            return None
        return Target(slug=urlsplit(o).netloc.split(".")[0], careers_url=careers_url, api_url=f"{o}/apply")

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        o = _origin(target.api_url) or _origin(target.careers_url)
        if not o:
            raise ProviderError("jazzhr needs an https <tenant>.applytojob.com url")
        board = f"{o}/apply"
        rows = parse_list(ctx.http.get_text(board, headers={"Accept": "text/html"}), board)
        company = target.company or urlsplit(o).netloc.split(".")[0]
        jobs = []
        for r in rows[: ctx.max_jobs]:
            jobs.append(self.job(title=r["title"], url=r["url"], company=company, location=r["location"],
                                 source_id=r["url"].rstrip("/").rsplit("/", 2)[-2] if r["url"].count("/") > 4 else "").validate())
        return jobs


PROVIDER = JazzHR()
