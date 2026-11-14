"""Magneto365 (LatAm) — server-rendered listing cards (<article class="card-jobs">).

Target: options.url / careers_url = https://www.magneto365.com/<cc>/empleos[...]
Mechanism from career-ops providers/magneto.mjs (MIT); code is our own.
"""
from __future__ import annotations

import html as _html
import re
from urllib.parse import urljoin, urlsplit, urlencode, parse_qsl

from ._base import Context, Job, Provider, ProviderError, Target

HOSTS = {"www.magneto365.com", "magneto365.com"}
POSTING = re.compile(r"^/[a-z]{2}/empleos/[a-z0-9-]+-(\d+)/?$", re.I)
ANCHOR = re.compile(r'<a\b[^>]*\bhref="([^"]+)"[^>]*>(.*?)</a>', re.I | re.S)
PAGE_PARAM = "paginator[page]"


def _clean(s) -> str:
    return re.sub(r"\s+", " ", _html.unescape(re.sub(r"<[^>]*>", " ", s or ""))).strip()


def parse_cards(html: str, origin: str) -> list[dict]:
    out = []
    for chunk in re.split(r"<article\b", html, flags=re.I)[1:]:
        card = re.split(r"</article>", chunk, flags=re.I)[0]
        if "card-jobs" not in card[: card.find(">") + 1]:
            continue
        hit = None
        for a in ANCHOR.finditer(card):
            u = urlsplit(urljoin(origin, _html.unescape(a.group(1))))
            m = POSTING.match(u.path) if u.netloc in HOSTS else None
            if m:
                hit = (u, m.group(1), a.group(2))
                break
        if not hit:
            continue
        u, jid, title_html = hit
        title = _clean(title_html)
        if len(title) < 3:
            continue
        h3 = re.search(r"<h3\b[^>]*>(.*?)</h3>", card, re.I | re.S)
        named = _clean(h3.group(1)).split(" | ")[0].strip() if h3 else ""
        if re.match(r"^(?:confidencial|empresa confidencial|magneto(?: empleos| 365)?)$", named, re.I):
            named = ""
        paras = [_clean(p) for p in re.findall(r"<p\b[^>]*>(.*?)</p>", card, re.I | re.S)]
        last = paras[-1] if paras else ""
        out.append({"id": jid, "title": title, "url": f"{u.scheme}://{u.netloc}{u.path}",
                    "company": named, "location": "" if last.startswith("$") else last})
    return out


class Magneto(Provider):
    name = "magneto"
    wave = "W5"
    kind = "board"
    tenant = False
    hosts = ("www.magneto365.com", "magneto365.com")

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        raw = target.options.get("url") or target.careers_url or "https://www.magneto365.com/co/empleos"
        p = urlsplit(raw)
        if p.scheme != "https" or p.netloc not in HOSTS:
            raise ProviderError(f"magneto: not a magneto365.com URL: {raw}")
        origin = f"https://{p.netloc}"
        base_q = [(k, v) for k, v in parse_qsl(p.query) if k != PAGE_PARAM]
        pages = min(int(target.options.get("max_pages") or 3), 20)
        cap = min(int(target.options.get("max_jobs") or 100), 500, ctx.max_jobs)
        jobs: list[Job] = []
        seen: set[str] = set()
        for page in range(1, pages + 1):
            url = f"{origin}{p.path}?{urlencode(base_q + [(PAGE_PARAM, str(page))])}"
            html = ctx.http.get_text(url)
            cards = parse_cards(html, origin)
            if not cards:
                if page == 1 and re.search(r'href="[^"]*/[a-z]{2}/empleos/[a-z0-9-]+-\d+/?"', html, re.I):
                    raise ProviderError("magneto: postings linked but no card parsed (markup change?)")
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


PROVIDER = Magneto()
