"""Built In — public search pages (HTML + schema.org ItemList), no auth.

GET https://builtin.com/jobs?search=<q>&page=N   (city markets: builtinnyc.com etc.)
Mechanism from career-ops providers/builtin.mjs (MIT); code is our own.
Simplified: ItemList rows joined to card markup for company / location / pay / age.
Config: Target.query (search), options host, scope, categories[], max_pages.
"""
from __future__ import annotations

import html
import json
import re
from datetime import datetime, timedelta, timezone
from urllib.parse import quote, urlsplit

from ._base import Context, Job, Provider, ProviderError, Target

HOSTS = {"builtin.com": "builtin.com"}
for _c in ("seattle.com", "nyc.com", "sf.com", "la.com", "boston.com", "austin.com", "chicago.org", "colorado.com"):
    _h = "builtin" + _c
    HOSTS[_h] = HOSTS["www." + _h] = "www." + _h
HOSTS["www.builtin.com"] = "builtin.com"

ITEM = re.compile(r'\{"@type":"ListItem","position":\d+,"name":("(?:[^"\\]|\\.)*"),"url":("(?:[^"\\]|\\.)*")(?:,"description":("(?:[^"\\]|\\.)*"))?\}')
CARD = re.compile(r'data-id="job-card-title"')
CARD_ID = re.compile(r'data-builtin-track-job-id="(\d+)"')
COMPANY = re.compile(r'<a[^>]+href="/company/[^"]*"[^>]*>([\s\S]{0,240}?)</a>')
TOOLTIP = re.compile(r'aria-label="Job locations"[^>]*data-bs-title="([^"]*)"')
MODES = {"remote or hybrid": "Remote or Hybrid", "remote": "Remote", "hybrid": "Hybrid", "in-office": "In-Office"}
BAND = re.compile(r"^(\d+(?:\.\d+)?)K(?:-(\d+(?:\.\d+)?)K)?\s+Annually$", re.I)


def _text(s: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]*>", " ", s))).strip()


def _after_icon(seg: str, icon: str) -> str:
    at = seg.find(icon)
    if at < 0:
        return ""
    for m in re.finditer(r">([^<>]+)<", seg[at:at + 600]):
        t = _text(m.group(1))
        if t:
            return t
    return ""


def _age(text: str) -> str:
    t = re.sub(r"^reposted\s+", "", (text or "").strip(), flags=re.I)
    now = datetime.now(timezone.utc)
    if re.fullmatch(r"today", t, re.I):
        return now.date().isoformat()
    if re.fullmatch(r"yesterday", t, re.I):
        return (now - timedelta(days=1)).date().isoformat()
    m = re.fullmatch(r"(\d+|an?)\+?\s+(minute|hour|day|week|month|year)s?\s+ago", t, re.I)
    if not m:
        return ""
    n = 1 if m.group(1).lower() in ("a", "an") else int(m.group(1))
    days = {"minute": 0, "hour": 0, "day": 1, "week": 7, "month": 30, "year": 365}[m.group(2).lower()]
    return (now - timedelta(days=n * days)).date().isoformat()


def parse_cards(page: str) -> dict[str, dict]:
    starts = [m.start() for m in CARD.finditer(page)]
    out: dict[str, dict] = {}
    for i, st in enumerate(starts):
        seg = page[st:min(starts[i + 1] if i + 1 < len(starts) else len(page), st + 12000)]
        idm = CARD_ID.search(seg)
        if not idm:
            continue
        pre = page[max(0, st - 2500) if i == 0 else starts[i - 1]:st]
        comps = COMPANY.findall(pre)
        mode = MODES.get(_after_icon(seg, "fa-house-building").lower(), "")
        loc = _after_icon(seg, "fa-location-dot")
        places = [loc] if loc and not re.match(r"^\d+\s+Locations?$", loc, re.I) else []
        if not places:
            tip = TOOLTIP.search(seg)
            if tip:
                places = [_text(x) for x in re.split(r"</div>|<br\s*/?>", html.unescape(tip.group(1)), flags=re.I) if _text(x)]
        pay = BAND.match(_after_icon(seg, "fa-sack-dollar"))
        rec = {"company": _text(comps[-1]) if comps else "", "places": places, "mode": mode,
               "posted": _age(_after_icon(seg, "fa-clock"))}
        if pay:
            lo = float(pay.group(1)) * 1000
            rec["pay"] = (lo, float(pay.group(2)) * 1000 if pay.group(2) else lo)
        out[idm.group(1)] = rec
    return out


class BuiltIn(Provider):
    name = "builtin"
    wave = "W1"
    kind = "board"
    tenant = False
    hosts = tuple(sorted(set(HOSTS.values())))

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        opts = target.options
        raw = str(opts.get("host") or "builtin.com").lower()
        if "/" in raw:
            raw = urlsplit(raw if "://" in raw else "https://" + raw).netloc
        host = HOSTS.get(raw)
        if not host:
            raise ProviderError(f"builtin: unknown market host {raw!r}")
        scope = str(opts.get("scope") or "").lower()
        scope = scope if re.fullmatch(r"[a-z0-9-]+", scope) else ""
        prefix = f"/jobs/{scope}" if scope else "/jobs"
        bases = []
        if target.query:
            bases.append(f"{prefix}?search={quote(target.query)}")
        bases += [f"{prefix}/{quote(str(c))}" for c in opts.get("categories") or []]
        if not bases:
            raise ProviderError("builtin needs a query or categories")
        max_pages = min(int(opts.get("max_pages", 3)), 25)
        seen: set[str] = set()
        jobs: list[Job] = []
        for base in bases:
            sep = "&" if "?" in base else "?"
            for pg in range(1, max_pages + 1):
                try:
                    page = ctx.http.get_text(f"https://{host}{base}{sep}page={pg}")
                except ProviderError:
                    break
                cards = parse_cards(page)
                added = rows = 0
                for m in ITEM.finditer(page):
                    try:
                        title, url = json.loads(m.group(1)), json.loads(m.group(2))
                        desc = json.loads(m.group(3)) if m.group(3) else ""
                    except ValueError:
                        continue
                    rows += 1
                    if not title or not url or url in seen:
                        continue
                    seen.add(url)
                    added += 1
                    jid = (re.search(r"/(\d+)(?:[/?#]|$)", url) or [None, ""])[1]
                    c = cards.get(jid, {})
                    mode, places = c.get("mode", ""), c.get("places", [])
                    loc = " · ".join(x for x in [mode, *places] if x) if places else (mode if "remote" in mode.lower() else "")
                    extra = {}
                    if c.get("pay"):
                        extra = dict(salary_min=c["pay"][0], salary_max=c["pay"][1], salary_period="year")
                    jobs.append(self.job(
                        title=title, url=url, company=c.get("company", ""), location=loc, locations=places,
                        workplace={"Remote": "remote", "Hybrid": "hybrid", "In-Office": "onsite"}.get(mode, ""),
                        posted_at=c.get("posted", ""), description=desc, source_id=jid, **extra,
                    ).validate())
                    if len(jobs) >= ctx.max_jobs:
                        return jobs
                if rows == 0 or added == 0:
                    break
        return jobs


PROVIDER = BuiltIn()
