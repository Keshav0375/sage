"""Dassault Systèmes — Exalead card_search_api (XML) on www.3ds.com.

Mechanism from career-ops providers/dassault.mjs (MIT); code is our own.
"""
from __future__ import annotations

import html
import re
from urllib.parse import urlencode, urlsplit

from ._base import Context, Job, Provider, Target
from ._parse import to_iso

BASE = "https://www.3ds.com/apisearch/card_search_api"
REFINES = ["f/card_content_type/career", "f/card_content_categories_facet/cards language/en"]
PAGE_SIZE = 10
MAX_PAGES = 60
CITY = {"City", "Ciudad", "Ville"}
COUNTRY = {"Country", "País", "Pais", "Pays"}
LABELS = ["Category", "Type", "Country", "City", "Products", "Year", "Categoría", "Categoria", "Tipo",
          "País", "Pais", "Ciudad", "Productos", "Año", "Ano", "Área", "Area", "Catégorie", "Pays",
          "Ville", "Produits", "Année", "Annee"]
LABEL_RE = re.compile(r"(^|\s)(" + "|".join(LABELS) + r")/")
META_RE = re.compile(r'<Meta name="([^"]+)"[^>]*>\s*<MetaString[^>]*name="value"[^>]*>([\s\S]*?)</MetaString>')


def _is_3ds(url: str) -> bool:
    h = urlsplit(url or "").netloc.lower()
    return h == "3ds.com" or h.endswith(".3ds.com")


def _city_country(cats: str) -> tuple[str, str]:
    marks = [(m.group(2), m.start() + len(m.group(1)), m.end()) for m in LABEL_RE.finditer(cats)]
    city = country = ""
    for i, (label, _ks, vs) in enumerate(marks):
        end = marks[i + 1][1] if i + 1 < len(marks) else len(cats)
        val = html.unescape(cats[vs:end]).strip()
        if not city and label in CITY:
            city = val
        elif not country and label in COUNTRY:
            country = val
    return city, country


class Dassault(Provider):
    name = "dassault"
    wave = "W6"
    kind = "company"
    tenant = False
    hosts = ("3ds.com",)

    def detect(self, careers_url: str):
        return Target(careers_url=careers_url) if _is_3ds(careers_url) else None

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        jobs: list[Job] = []
        seen: set[str] = set()
        for page in range(MAX_PAGES):
            q = [("lang", "en")] + [("r", r) for r in REFINES] + [("start", str(page * PAGE_SIZE))]
            xml = ctx.http.get_text(f"{BASE}?{urlencode(q)}", headers={"Accept": "application/xml"})
            hits = re.findall(r"<Hit\b[\s\S]*?</Hit>", xml)
            if not hits:
                break
            fresh = 0
            for hit in hits:
                meta: dict[str, str] = {}
                for k, v in META_RE.findall(hit):
                    meta.setdefault(k, v)
                title = " ".join(html.unescape(re.sub(r"<[^>]*>", " ", meta.get("content_title", ""))).split())
                url = html.unescape(meta.get("content_cta_1_url", "").strip())
                if not title or not _is_3ds(url):
                    continue
                cid = meta.get("card_id", "").strip() or url
                if cid in seen:
                    continue
                seen.add(cid)
                fresh += 1
                city, country = _city_country(meta.get("content_categories", ""))
                ts = (meta.get("content_start_datetime") or meta.get("card_update_timestamp") or "").strip()
                m = re.match(r"(\d{4})/(\d{2})/(\d{2})[ T](\d{2}:\d{2}:\d{2})", ts)
                posted = to_iso(f"{m[1]}-{m[2]}-{m[3]}T{m[4]}+00:00") if m else ""
                jobs.append(self.job(title=title, url=url, company=target.company or "Dassault Systèmes",
                                     location=city or country, country="" if city else country,
                                     posted_at=posted, source_id=cid).validate())
                if len(jobs) >= ctx.max_jobs:
                    return jobs
            if not fresh:
                break
        return jobs


PROVIDER = Dassault()
