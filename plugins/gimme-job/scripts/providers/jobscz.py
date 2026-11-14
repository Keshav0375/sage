"""Jobs.cz (CZ) — server-rendered search result cards.

GET https://www.jobs.cz/prace/[<location>/]?q[]=<keyword>&page=N
Mechanism from career-ops providers/jobscz.mjs (MIT); code is our own.
"""
from __future__ import annotations

import html as _html
import re
from datetime import date, timedelta
from urllib.parse import quote

from ._base import Context, Job, Provider, ProviderError, Target

SEARCH = "https://www.jobs.cz/prace/"
POSTING = "https://www.jobs.cz/rpd/"
PAGE_SIZE = 30
MONTHS = ["ledna", "února", "března", "dubna", "května", "června", "července", "srpna",
          "září", "října", "listopadu", "prosince"]


def _clean(s) -> str:
    return re.sub(r"\s+", " ", _html.unescape(re.sub(r"<[^>]*>", " ", s or ""))).strip()


def posted_date(text: str, today: date) -> str:
    m = re.match(r"^(\d{1,2})\.\s*(\w+)$", text or "")
    if m and m.group(2) in MONTHS:
        d = date(today.year, MONTHS.index(m.group(2)) + 1, int(m.group(1)))
        return (d.replace(year=today.year - 1) if d > today else d).isoformat()
    if text == "Přidáno dnes":
        return today.isoformat()
    if text == "Přidáno včera":
        return (today - timedelta(days=1)).isoformat()
    return ""


def parse_page(html: str) -> tuple[int, list[dict]]:
    cards = re.split(r'<article\s+class="SearchResultCard[^"]*"', html)[1:]
    text = _clean(html)
    if not cards:
        if "Nenašli jsme žádné nabídky" in text:
            return 0, []
        raise ProviderError("jobscz: no result cards and no empty-result notice (markup changed?)")
    rows = []
    today = date.today()
    for c in cards:
        i = re.search(r'data-jobad-id="(\d+)"', c)
        t = re.search(r'data-test-ad-title="([^"]*)"', c)
        title = _clean(t.group(1)) if t else ""
        if not i or not title:
            continue
        st = re.search(r'data-test-ad-status="[^"]*"[^>]*>([^<]*)<', c)
        co = re.search(r'<span translate="no">(.*?)</span>', c, re.S)
        lo = re.search(r'data-test="serp-locality"[^>]*>(.*?)</li>', c, re.S)
        rows.append({"id": i.group(1), "title": title, "url": f"{POSTING}{i.group(1)}/",
                     "company": _clean(co.group(1)) if co else "", "location": _clean(lo.group(1)) if lo else "",
                     "posted": posted_date(_clean(st.group(1)), today) if st else ""})
    m = re.search(r"Našli jsme\s+([\d\s]+?)\s*nabídk?", text) or re.search(r"Našli jsme\s+([\d\s]+?)\s*nab", text)
    total = int(re.sub(r"\D", "", m.group(1))) if m and re.sub(r"\D", "", m.group(1)) else len(rows)
    return total, rows


class JobsCz(Provider):
    name = "jobscz"
    wave = "W5"
    kind = "board"
    tenant = False
    hosts = ("www.jobs.cz",)

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        kws = target.options.get("keywords") or [k.strip() for k in (target.query or "").split(",") if k.strip()]
        if isinstance(kws, str):
            kws = [kws]
        if not kws:
            raise ProviderError("jobscz needs keywords (target.query or options.keywords)")
        loc = (target.location or target.options.get("location") or "").strip()
        max_pages = min(int(target.options.get("max_pages") or 3), 20)
        seen: dict[str, Job] = {}
        for kw in kws:
            last = 1
            page = 1
            while page <= last:
                url = f"{SEARCH}{quote(loc) + '/' if loc else ''}?q%5B%5D={quote(kw)}" + (f"&page={page}" if page > 1 else "")
                total, rows = parse_page(ctx.http.get_text(url))
                if page == 1:
                    last = min(-(-total // PAGE_SIZE), max_pages)
                if not rows:
                    break
                for r in rows:
                    if r["url"] not in seen:
                        seen[r["url"]] = self.job(title=r["title"], url=r["url"], company=r["company"],
                                                  location=r["location"], country="CZ", posted_at=r["posted"],
                                                  source_id=r["id"]).validate()
                        if len(seen) >= ctx.max_jobs:
                            return list(seen.values())
                page += 1
        return list(seen.values())


PROVIDER = JobsCz()
