"""getManfred (ES) — public v2 offers feed (JSON array).

GET https://www.getmanfred.com/api/v2/public/offers?lang=EN|ES
Mechanism from career-ops providers/manfred.mjs (MIT); code is our own.
"""
from __future__ import annotations

import re
from urllib.parse import quote

from ._base import Context, Job, Provider, ProviderError, Target

FEED = "https://www.getmanfred.com/api/v2/public/offers"
OFFER = "https://www.getmanfred.com/ofertas-empleo"
SYMBOLS = {"€": "EUR", "£": "GBP", "US$": "USD", "$": "USD", "MXN$": "MXN"}


def currency(raw) -> str:
    if not isinstance(raw, str):
        return ""
    c = re.sub(r"\s", "", raw).upper()
    for sym, iso in SYMBOLS.items():
        if c == sym.upper():
            return iso
    return c if re.fullmatch(r"[A-Z]{3}", c) else ""


class Manfred(Provider):
    name = "manfred"
    wave = "W5"
    kind = "board"
    tenant = False
    hosts = ("www.getmanfred.com",)

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        lang = str(target.options.get("lang") or "EN").upper()
        lang = lang if lang in ("EN", "ES") else "EN"
        data = ctx.http.get_json(f"{FEED}?lang={lang}")
        if not isinstance(data, list):
            raise ProviderError("manfred: unexpected response, expected a JSON array")
        kw = (target.query or "").lower().split()
        jobs: list[Job] = []
        for o in data:
            if o.get("status") != "ACTIVE":
                continue
            title = str(o.get("position") or "").strip()
            slug = str(o.get("slug") or "").strip()
            try:
                oid = int(o.get("id"))
            except (TypeError, ValueError):
                continue
            if not title or not slug or oid <= 0:
                continue
            if kw and not all(w in title.lower() for w in kw):
                continue
            locs = [l.strip() for l in o.get("locations") or [] if isinstance(l, str) and l.strip()]
            remote = o.get("remotePercentage")
            workplace = ""
            if isinstance(remote, (int, float)):
                workplace = "remote" if remote >= 100 else ("hybrid" if remote > 0 else "")
            lo = o.get("salaryFrom") if isinstance(o.get("salaryFrom"), (int, float)) and o.get("salaryFrom") > 0 else None
            hi = o.get("salaryTo") if isinstance(o.get("salaryTo"), (int, float)) and o.get("salaryTo") > 0 else None
            kw2 = {}
            if lo is not None or hi is not None:
                kw2 = {"salary_min": lo if lo is not None else hi, "salary_max": hi if hi is not None else lo,
                       "currency": currency(o.get("currency"))}
            jobs.append(self.job(
                title=title, url=f"{OFFER}/{oid}/{quote(slug, safe='')}",
                company=str((o.get("company") or {}).get("name") or "").strip(),
                location=", ".join(locs) or {"remote": "Remote", "hybrid": "Hybrid"}.get(workplace, ""),
                locations=locs, workplace=workplace, source_id=str(oid), **kw2,
            ).validate())
            if len(jobs) >= ctx.max_jobs:
                break
        return jobs


PROVIDER = Manfred()
