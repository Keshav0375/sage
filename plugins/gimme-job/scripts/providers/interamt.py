"""Interamt (German public-sector jobs) — best-effort plain-HTTP read of the result table.

Mechanism from career-ops scan-interamt.mjs (MIT). Upstream drives Playwright because Interamt is a
stateful Apache Wicket app with no API. SIMPLIFIED: stdlib only, so we fetch the entry page once and
parse any ``tr.ia-e-table__row`` rows the server renders; when none are present (the usual case without a
browser session) we warn and return []. Keyword search needs a browser and is not ported.
"""
from __future__ import annotations

import html
import re
from urllib.parse import urlsplit

from ._base import Context, Job, Provider, Target
from ._parse import to_iso

HOME = "https://interamt.de/koop/app/"
OFFER = "https://interamt.de/koop/app/stelle?id="
ROW_RE = re.compile(r'<tr\b[^>]*class="[^"]*ia-e-table__row[^"]*"[^>]*>([\s\S]*?)</tr>', re.I)


def _clean(s: str) -> str:
    return " ".join(html.unescape(re.sub(r"<[^>]*>", " ", s or "")).split())


def _cell(row: str, field: str) -> str:
    m = re.search(rf'<td\b[^>]*data-field="{field}"[^>]*>([\s\S]*?)</td>', row, re.I)
    return _clean(m.group(1)) if m else ""


class Interamt(Provider):
    name = "interamt"
    wave = "W6"
    kind = "public"
    tenant = False
    hosts = ("interamt.de",)

    def detect(self, careers_url: str):
        h = urlsplit(careers_url or "").netloc.lower()
        return Target(careers_url=careers_url) if h in ("interamt.de", "www.interamt.de") else None

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        page = ctx.http.get_text(HOME)
        jobs: list[Job] = []
        seen: set[str] = set()
        for m in ROW_RE.finditer(page):
            row = m.group(1)
            title = _cell(row, "Stellenbezeichnung")
            idm = re.search(r'data-field="StellenangebotId"[^>]*>[\s\S]*?<span[^>]*>([\s\S]*?)</span>', row, re.I)
            jid = _clean(idm.group(1)) if idm else ""
            if not title or not jid or jid in seen:
                continue
            seen.add(jid)
            pub = _cell(row, "Von")
            dm = re.match(r"(\d{1,2})\.(\d{1,2})\.(\d{4})$", pub)
            posted = f"{dm[3]}-{int(dm[2]):02d}-{int(dm[1]):02d}" if dm else ""
            dl = _cell(row, "Bewerbungsfrist")
            dd = re.match(r"(\d{1,2})\.(\d{1,2})\.(\d{4})$", dl)
            closes = f"{dd[3]}-{int(dd[2]):02d}-{int(dd[1]):02d}" if dd else ""
            loc = " ".join(x for x in [_cell(row, "Dienstort"), _cell(row, "PLZOrte")] if x)
            jobs.append(self.job(title=title, url=OFFER + jid, company=_cell(row, "Behoerde") or "Interamt",
                                 location=loc, posted_at=posted, closes_at=closes, country="DE",
                                 source_id=jid).validate())
            if len(jobs) >= ctx.max_jobs:
                break
        if not jobs:
            ctx.warn("interamt: no result rows in the plain HTTP response (search needs a browser session)")
        return jobs


PROVIDER = Interamt()
