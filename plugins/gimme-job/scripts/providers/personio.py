"""Personio — public XML job feed (no auth).

GET https://{slug}.jobs.personio.de/xml   (also .jobs.personio.com)
Mechanism from career-ops providers/personio.mjs (MIT); code is our own.
Simplified: XML feed only (no Next.js page payload path).
"""
from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from urllib.parse import urlsplit

from ._base import Context, Job, Provider, ProviderError, Target
from ._parse import employment_from, to_iso

HOST_RE = re.compile(r"^([a-z0-9][a-z0-9-]*)\.jobs\.personio\.(de|com)$")


def _t(el, tag: str) -> str:
    c = el.find(tag)
    return (c.text or "").strip() if c is not None else ""


class Personio(Provider):
    name = "personio"
    wave = "W1"
    kind = "ats"
    tenant = True
    hosts = ("jobs.personio.de", "jobs.personio.com")

    def detect(self, careers_url: str):
        host = urlsplit(careers_url or "").netloc.lower()
        if not HOST_RE.match(host):
            return None
        return Target(slug=host.split(".")[0], careers_url=careers_url, api_url=f"https://{host}/xml")

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        t = target if target.api_url else (self.detect(target.careers_url) or target)
        host = urlsplit(t.api_url).netloc if t.api_url else (f"{t.slug}.jobs.personio.de" if t.slug else "")
        if not host:
            raise ProviderError("personio needs a slug or jobs.personio url")
        try:
            root = ET.fromstring(ctx.http.get_text(f"https://{host}/xml").lstrip("﻿").strip())
        except ET.ParseError as e:
            raise ProviderError(f"personio: bad XML: {e}") from e
        jobs: list[Job] = []
        for pos in root.iter("position"):
            pid, title = _t(pos, "id"), _t(pos, "name")
            if not title or not pid.isdigit():
                continue
            offices = []
            for o in [pos.find("office")] + list(pos.findall("additionalOffices/office")):
                s = (o.text or "").strip() if o is not None else ""
                if s and s not in offices:
                    offices.append(s)
            jobs.append(self.job(
                title=title, url=f"https://{host}/job/{pid}",
                company=target.company or t.slug or host.split(".")[0],
                locations=offices, department=_t(pos, "department"),
                employment=employment_from(_t(pos, "employmentType")),
                posted_at=to_iso(_t(pos, "createdAt")), source_id=pid,
            ).validate())
            if len(jobs) >= ctx.max_jobs:
                break
        return jobs


PROVIDER = Personio()
