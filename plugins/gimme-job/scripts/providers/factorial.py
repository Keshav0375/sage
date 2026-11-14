"""Factorial careers sites — server-rendered board at https://<tenant>.factorial.com/.

Mechanism from career-ops providers/factorial.mjs (MIT); code is our own.
"""
from __future__ import annotations

import html as htmllib
import re
from urllib.parse import urlsplit

from ._base import Context, Job, Provider, ProviderError, Target

DOMAINS = (
    "factorial.ae", "factorial.be", "factorial.ch", "factorial.co", "factorial.com", "factorial.es",
    "factorial.fr", "factorial.it", "factorial.ke", "factorial.mx", "factorial.pl", "factorial.rs",
    "factorialhr.ar", "factorialhr.cl", "factorialhr.co", "factorialhr.co.uk", "factorialhr.com",
    "factorialhr.com.ar", "factorialhr.com.br", "factorialhr.com.de", "factorialhr.de", "factorialhr.pt",
)
LABEL = re.compile(r"^[a-z0-9][a-z0-9-]*$")
NOT_BOARD = {"www", "app", "api", "help", "blog"}
POSTING = re.compile(r"/job_posting/[a-z0-9-]+", re.I)


def _split(host: str):
    host = (host or "").lower()
    for d in DOMAINS:
        if host.endswith("." + d):
            t = host[: -(len(d) + 1)]
            if not LABEL.match(t) or t in NOT_BOARD:
                return None
            return t, d
    return None


def _origin(url: str) -> str:
    p = urlsplit((url or "").strip())
    if p.scheme != "https":
        return ""
    s = _split(p.hostname or "")
    if not s:
        return ""
    d = "factorial.com" if s[1] == "factorialhr.com" else s[1]
    return f"https://{s[0]}.{d}"


def _text(h: str) -> str:
    return re.sub(r"\s+", " ", htmllib.unescape(re.sub(r"<[^>]*>", " ", h))).strip()


def _attr(tag: str, name: str) -> str:
    m = re.search(r"\s%s=(?:'([^']*)'|\"([^\"]*)\")" % re.escape(name), tag)
    return htmllib.unescape(m.group(1) or m.group(2) or "") if m else ""


class Factorial(Provider):
    name = "factorial"
    wave = "W4"
    kind = "ats"
    tenant = True
    hosts = tuple(DOMAINS)

    def detect(self, careers_url: str):
        o = _origin(careers_url)
        if not o:
            return None
        return Target(slug=urlsplit(o).hostname.split(".")[0], careers_url=careers_url, api_url=o + "/")

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        o = _origin(target.api_url) or _origin(target.careers_url)
        if not o:
            raise ProviderError("factorial needs https://<tenant>.factorialhr.com or .factorial.com")
        html = ctx.http.get_text(o + "/")
        s = _split(urlsplit(o).hostname)
        tenant = s[0] if s else ""
        by_url: dict[str, dict] = {}
        parts = re.split(r"data-target=['\"]job-filters\.officeGroup['\"]", html)
        for i, part in enumerate(parts):
            heading = ""
            if i:
                hm = re.search(r"<h3[^>]*>([\s\S]*?)</h3>", part)
                heading = _text(hm.group(1)) if hm else ""
            for card in re.split(r"<li\s+class=['\"]job-offer-item\b", part)[1:]:
                tag = card[: card.find(">") + 1]
                raw = _attr(tag, "data-job-postings-url")
                u = urlsplit(raw)
                if u.scheme != "https" or not POSTING.search(u.path):
                    continue
                us = _split(u.hostname or "")
                if not tenant or not us or us[0] != tenant:
                    continue
                tm = re.search(r"factorial__headingFontFamily[^>]*>([\s\S]*?)</", card)
                title = _text(tm.group(1)) if tm else ""
                if not title:
                    continue
                office = heading or re.sub(r"^city:", "", _attr(tag, "data-location-key"))
                e = by_url.setdefault(raw, {"title": title, "offices": [], "remote": False, "id": ""})
                idm = re.search(r"-(\d+)/?$", u.path)
                if idm:
                    e["id"] = idm.group(1)
                if office and office not in e["offices"]:
                    e["offices"].append(office)
                e["remote"] = e["remote"] or _attr(tag, "data-is-remote") == "true"
        if not by_url and POSTING.search(html):
            raise ProviderError("factorial: board links postings but none could be parsed")
        jobs: list[Job] = []
        for url, e in list(by_url.items())[: ctx.max_jobs]:
            places = [" / ".join(e["offices"])]
            if e["remote"] and not any(re.search(r"\bremote\b", x, re.I) for x in e["offices"]):
                places.append("Remote")
            jobs.append(self.job(
                title=e["title"], url=url, company=target.company or tenant,
                location=" · ".join(p for p in places if p),
                workplace="remote" if e["remote"] else "", source_id=e["id"],
            ).validate())
        return jobs


PROVIDER = Factorial()
