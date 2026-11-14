"""OCC Mundial (Mexico) — server-rendered search pages, board-wide keyword scan.

GET https://www.occ.com.mx/empleos/de-<kw>[-pagina-N]/[en-<state>/]
Mechanism from career-ops providers/occ.mjs (MIT); code is our own.
"""
from __future__ import annotations

import re
import unicodedata

from ._base import Context, Job, Provider, ProviderError, Target
from ._parse import html_to_text

ORIGIN = "https://www.occ.com.mx"


def _slug(s: str) -> str:
    s = unicodedata.normalize("NFD", str(s))
    s = "".join(c for c in s if not unicodedata.combining(c)).lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def _txt(h: str) -> str:
    return html_to_text(re.sub(r"<[^>]+>", " ", h)).replace("\n", " ").strip()


def search_url(query: str, state: str, page: int) -> str:
    q = _slug(query)
    kw = f"de-{q}-pagina-{page}" if page > 1 else f"de-{q}"
    st = f"en-{_slug(state)}/" if state else ""
    return f"{ORIGIN}/empleos/{kw}/{st}"


def parse_cards(html: str) -> list[dict]:
    out = []
    for chunk in html.split('class="card-job-offer')[1:]:
        m = re.search(r"data-id='(\d+)'", chunk)
        t = re.search(r"<h2[^>]*>([\s\S]*?)</h2>", chunk)
        if not m or not t or not _txt(t.group(1)):
            continue
        c = re.search(r"h-\[21px\][^>]*>\s*<span[^>]*>([\s\S]*?)</span>", chunk)
        loc = re.search(r"no-alter-loc-text[^>]*>[\s\S]*?<p[^>]*>([\s\S]*?)</p>", chunk)
        company = _txt(c.group(1)) if c else ""
        out.append({"id": m.group(1), "title": _txt(t.group(1)),
                    "company": "" if re.match(r"(?i)empresa confidencial$", company) else company,
                    "location": _txt(loc.group(1)) if loc else ""})
    return out


class Occ(Provider):
    name = "occ"
    wave = "W5"
    kind = "board"
    tenant = False
    hosts = ("www.occ.com.mx",)

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        o = target.options
        raw = o.get("queries") or o.get("keywords") or target.query
        if isinstance(raw, str):
            raw = raw.replace("\n", ",").split(",")
        queries = [str(q).strip() for q in raw or [] if str(q).strip()]
        if not queries:
            raise ProviderError("occ needs target.query / options.queries (keyword search board)")
        states = o.get("states") or ([target.location] if target.location else [""])
        max_pages = min(int(o.get("max_pages") or 3), 10)
        jobs: dict[str, Job] = {}
        for q in queries:
            for st in states:
                for page in range(1, max_pages + 1):
                    cards = parse_cards(ctx.http.get_text(search_url(q, st, page)))
                    fresh = 0
                    for c in cards:
                        if c["id"] in jobs:
                            continue
                        fresh += 1
                        jobs[c["id"]] = self.job(
                            title=c["title"], url=f"{ORIGIN}/empleo/oferta/{c['id']}/", company=c["company"],
                            location=c["location"], country="MX", source_id=c["id"]).validate()
                        if len(jobs) >= ctx.max_jobs:
                            return list(jobs.values())
                    if not fresh:
                        break
        return list(jobs.values())


PROVIDER = Occ()
