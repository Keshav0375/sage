"""Computrabajo (LatAm) — server-rendered listing cards (<article class="box_offer">).

Target: options.url (or target.careers_url) = https://<cc>.computrabajo.com/trabajo-de-<kw>
Mechanism from career-ops providers/computrabajo.mjs (MIT); code is our own.
Polite: at most 3 pages, 15 postings by default.
"""
from __future__ import annotations

import html as _html
import re
from urllib.parse import quote, urlsplit

from ._base import Context, Job, Provider, ProviderError, Target

HOST = re.compile(r"^[a-z]{2}\.computrabajo\.com$")
LINK = re.compile(r'<a\b[^>]*\bhref="((?:https://[a-z]{2}\.computrabajo\.com)?/ofertas-de-trabajo/[^"#?]+)[^"]*"[^>]*>(.*?)</a>', re.I | re.S)
COMPANY = re.compile(r'<a\b[^>]*\boffer-grid-article-company-url\b[^>]*>(.*?)</a>', re.I | re.S)
LOCATION = re.compile(r'<p\b[^>]*>\s*<span class="mr10">(.*?)</span>', re.I | re.S)


def _clean(s: str) -> str:
    return re.sub(r"\s+", " ", _html.unescape(re.sub(r"<[^>]*>", " ", s))).strip()


def parse_cards(html: str, origin: str) -> list[dict]:
    out = []
    for chunk in re.split(r"<article\b", html, flags=re.I)[1:]:
        card = re.split(r"</article>", chunk, flags=re.I)[0]
        open_tag = card[: card.find(">") + 1]
        if "box_offer" not in open_tag:
            continue
        link = LINK.search(card)
        if not link:
            continue
        path = link.group(1)
        url = path if path.startswith("http") else origin + path
        title = _clean(link.group(2))
        if len(title) < 3 or not HOST.match(urlsplit(url).netloc):
            continue
        idm = re.search(r"\bdata-id=['\"]([^'\"]+)['\"]", open_tag)
        c, loc = COMPANY.search(card), LOCATION.search(card)
        out.append({"id": idm.group(1) if idm else path, "title": title, "url": url,
                    "company": _clean(c.group(1)) if c else "", "location": _clean(loc.group(1)) if loc else ""})
    return out


class Computrabajo(Provider):
    name = "computrabajo"
    wave = "W5"
    kind = "board"
    tenant = False
    hosts = ("computrabajo.com",)

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        raw = target.options.get("url") or target.careers_url
        if not raw:
            cc = (target.options.get("country") or "co").lower()
            kw = quote((target.query or "").strip().lower().replace(" ", "-"))
            raw = f"https://{cc}.computrabajo.com/trabajo-de-{kw}" if kw else f"https://{cc}.computrabajo.com/empleos"
        p = urlsplit(raw)
        if p.scheme != "https" or not HOST.match(p.netloc):
            raise ProviderError(f"computrabajo: not a Computrabajo country host: {raw}")
        origin = f"https://{p.netloc}"
        pages = min(int(target.options.get("max_pages") or 3), 3)
        cap = min(int(target.options.get("max_jobs") or 15), 15, ctx.max_jobs)
        jobs: list[Job] = []
        seen: set[str] = set()
        for page in range(1, pages + 1):
            url = f"{origin}{p.path}?by=publicationtime&p={page}"
            html = ctx.http.get_text(url, headers={"Accept-Language": "es-CO,es;q=0.9,en;q=0.7"})
            cards = parse_cards(html, origin)
            if not cards:
                if page == 1 and "/ofertas-de-trabajo/" in html:
                    raise ProviderError("computrabajo: postings linked but no card parsed (markup change?)")
                break
            fresh = 0
            for c in cards:
                if c["id"] in seen:
                    continue
                seen.add(c["id"])
                fresh += 1
                jobs.append(self.job(title=c["title"], url=c["url"], company=c["company"],
                                     location=c["location"], source_id=c["id"]).validate())
                if len(jobs) >= cap:
                    return jobs
            if not fresh:
                break
        return jobs


PROVIDER = Computrabajo()
