"""Homerun — per-tenant public Atom feed https://feed.homerun.co/<slug>.

Mechanism from career-ops providers/homerun.mjs (MIT); code is our own.
"""
from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from urllib.parse import urlsplit

from ._base import Context, Job, Provider, ProviderError, Target
from ._parse import html_to_text, parse_salary, to_iso

FEED = "feed.homerun.co"
LABEL = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$", re.I)
TENANT = re.compile(r"^([a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?)\.homerun\.co$", re.I)
RESERVED = {"www", "app", "feed", "help", "static", "cdn", "api", "developers", "blog", "404"}


def _slug(url: str) -> str:
    p = urlsplit((url or "").strip())
    if p.scheme != "https":
        return ""
    host = (p.hostname or "").lower()
    if host == FEED:
        parts = [x for x in p.path.split("/") if x]
        slug = parts[0] if parts else ""
    else:
        m = TENANT.match(host)
        if not m or m.group(1).lower() in RESERVED:
            return ""
        slug = m.group(1)
    return slug.lower() if LABEL.match(slug) else ""


def _loc(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _child(el, name: str):
    for c in el:
        if _loc(c.tag) == name:
            return c
    return None


def _text(el, name: str) -> str:
    c = _child(el, name)
    return (c.text or "").strip() if c is not None else ""


class Homerun(Provider):
    name = "homerun"
    wave = "W4"
    kind = "ats"
    tenant = True
    hosts = ("homerun.co",)

    def detect(self, careers_url: str):
        s = _slug(careers_url)
        return Target(slug=s, careers_url=careers_url, api_url=f"https://{FEED}/{s}") if s else None

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        slug = target.slug or _slug(target.api_url) or _slug(target.careers_url)
        if not slug:
            raise ProviderError("homerun needs a <slug>.homerun.co careers url")
        xml = ctx.http.get_text(f"https://{FEED}/{slug}")
        try:
            root = ET.fromstring(xml.lstrip("﻿").strip())
        except ET.ParseError as e:
            raise ProviderError(f"homerun: feed is not XML: {e}")
        if _loc(root.tag) != "feed":
            raise ProviderError("homerun: expected an Atom <feed>")
        jobs: list[Job] = []
        for e in root:
            if _loc(e.tag) != "entry":
                continue
            href = ""
            for c in e:
                if _loc(c.tag) == "link" and c.attrib.get("href"):
                    if c.attrib.get("rel", "alternate") == "alternate" or not href:
                        href = c.attrib["href"]
            author = _child(e, "author")
            loc = _child(e, "location")
            raw_sal = _text(e, "salary_indication")
            sal = parse_salary(re.sub(r"[€£$₹]", "", raw_sal).replace(" to ", " - "))
            sal = sal if sal and sal.get("salary_period") == "year" else {}
            if sal:
                sal["currency"] = sal.get("currency") or next(
                    (c for sym, c in (("€", "EUR"), ("£", "GBP"), ("$", "USD"), ("₹", "INR")) if sym in raw_sal), "")
            upd = _text(e, "updated")
            if re.fullmatch(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", upd):
                upd = upd.replace(" ", "T") + "+00:00"
            jobs.append(self.job(
                title=_text(e, "title"), url=href,
                company=target.company or (_text(author, "name") if author is not None else "") or slug,
                location=_text(loc, "name") if loc is not None else "",
                posted_at=to_iso(upd), description=html_to_text(_text(e, "description")),
                source_id=_text(e, "id"), **sal,
            ).validate())
            if len(jobs) >= ctx.max_jobs:
                break
        return jobs


PROVIDER = Homerun()
