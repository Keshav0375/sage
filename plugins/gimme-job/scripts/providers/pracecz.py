"""Prace.cz (Czech Republic) — Next.js flight data in search pages, board-wide.

GET https://www.prace.cz/nabidky/[<location>/]?q=<kw>&page=N  (self.__next_f.push chunks hold currentPageItems)
Mechanism from career-ops providers/pracecz.mjs (MIT); code is our own.
"""
from __future__ import annotations

import json
import re
from urllib.parse import quote, urlsplit

from ._base import Context, Job, Provider, ProviderError, Target
from ._parse import to_iso

SEARCH = "https://www.prace.cz/nabidky/"
POSTING = "https://www.prace.cz/nabidka/"
PAGE_SIZE = 40


def extract_results(html: str) -> tuple[int, list]:
    text = ""
    for m in re.finditer(r"self\.__next_f\.push\((\[[\s\S]*?\])\)</script>", html):
        try:
            chunk = json.loads(m.group(1))
        except ValueError:
            continue
        if len(chunk) > 1 and isinstance(chunk[1], str):
            text += chunk[1]
    total = re.search(r'"totalItems":(\d+)', text)
    key = re.search(r'"currentPageItems":\s*', text)
    if not total or not key or text[key.end():key.end() + 1] != "[":
        raise ProviderError("pracecz: currentPageItems/totalItems not found, page markup changed?")
    items, _ = json.JSONDecoder().raw_decode(text, key.end())
    return int(total.group(1)), items


def _career_url(raw: str) -> str:
    p = urlsplit(raw or "")
    if p.scheme == "https" and p.netloc.endswith(".jobs.cz"):
        return f"https://{p.netloc}{p.path}"
    return ""


class PraceCz(Provider):
    name = "pracecz"
    wave = "W5"
    kind = "board"
    tenant = False
    hosts = ("www.prace.cz",)

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        raw = target.options.get("keywords") or target.query
        if isinstance(raw, str):
            raw = raw.replace("\n", ",").split(",")
        kws = list(dict.fromkeys(str(x).strip() for x in raw or [] if str(x).strip()))
        if not kws:
            raise ProviderError("pracecz needs target.query / options.keywords")
        loc = (target.location or target.options.get("location") or "").strip()
        max_pages = min(int(target.options.get("max_pages") or 10), 1500)
        jobs: dict[str, Job] = {}
        for kw in kws:
            last = 1
            page = 1
            while page <= last:
                url = f"{SEARCH}{quote(loc) + '/' if loc else ''}?q={quote(kw)}" + (f"&page={page}" if page > 1 else "")
                total, items = extract_results(ctx.http.get_text(url))
                if not items:
                    break
                if page == 1:
                    last = min(-(-total // PAGE_SIZE), max_pages)
                for it in items:
                    adv = it.get("advert") or {}
                    meta = it.get("metadata") or {}
                    aid = meta.get("advertId")
                    title = (adv.get("title") or "").strip()
                    if aid is None or not title or str(aid) in jobs:
                        continue
                    work = adv.get("workLocation") or {}
                    places = [(p.get("city") or "").strip() for p in work.get("places") or [] if (p.get("city") or "").strip()]
                    remote = work.get("type") == "FULL_REMOTE"
                    if remote:
                        places.insert(0, "Remote")
                    sal = adv.get("salary") or {}
                    period = {"MONTH": "month", "YEAR": "year"}.get(sal.get("period"), "")
                    show = period and sal.get("displayMode") != "NO"
                    jobs[str(aid)] = self.job(
                        title=title,
                        url=_career_url(((it.get("extended") or {}).get("careerPage") or {}).get("url")) or f"{POSTING}{quote(str(aid))}/",
                        company=((it.get("company") or {}).get("publicName") or "").strip(),
                        location=", ".join(places), locations=places, country="CZ",
                        workplace="remote" if remote else "",
                        posted_at=to_iso(meta.get("publishedAt")), source_id=str(aid),
                        salary_min=sal.get("min") if show and (sal.get("min") or 0) > 0 else None,
                        salary_max=sal.get("max") if show and (sal.get("max") or 0) > 0 else None,
                        currency=str(sal.get("currency") or "").upper() if show else "",
                        salary_period=period if show else "",
                    ).validate()
                    if len(jobs) >= ctx.max_jobs:
                        return list(jobs.values())
                page += 1
        return list(jobs.values())


PROVIDER = PraceCz()
