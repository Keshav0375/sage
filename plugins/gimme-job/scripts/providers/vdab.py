"""VDAB (Flanders, Belgium) — public vindeenjob search API, board-wide.

POST https://www.vdab.be/rest/vindeenjob/v4/vacatureLight/zoek   header vej-key-monitor: <public site key>
The key is not hardcoded: read from options.vej_key / env GIMME_JOB_VDAB_KEY, else derived from the site's JS bundle.
Mechanism from career-ops providers/vdab.mjs (MIT); code is our own.
"""
from __future__ import annotations

import os
import re

from ._base import Context, Job, Provider, ProviderError, Target
from ._parse import to_iso

API = "https://www.vdab.be/rest/vindeenjob/v4/vacatureLight/zoek"
DETAIL_BASE = "https://www.vdab.be/vindeenjob/vacatures/"
KEY_RE = re.compile(r'vej-key-monitor","([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})"', re.I)
BUNDLE_RE = re.compile(r"https://www\.vdab\.be/webapps/vindeenjob/main-[\w-]+\.js")


def search_body(kw: str, days: int, size: int, page: int) -> dict:
    empty = ["diplomaCodes", "arbeidsduurCodes", "arbeidsregimeCodes", "contractTypeCodes", "jobdomeinCodes",
             "internationaalCodes", "beroepCodes", "ervaringCodes", "rijbewijsCodes", "attestCodes"]
    crit = {"trefwoord": kw, **{k: [] for k in empty}, "taalCriteria": {"taalSelecties": []},
            "onlineSindsCode": str(days), "sorteerVeld": "STANDAARD"}
    return {"criteria": crit, "pagina": page, "zoekmodus": "C2", "paginaGrootte": size}


class Vdab(Provider):
    name = "vdab"
    wave = "W5"
    kind = "board"
    tenant = False
    hosts = ("www.vdab.be",)

    def _key(self, target: Target, ctx: Context) -> str:
        key = target.options.get("vej_key") or os.environ.get("GIMME_JOB_VDAB_KEY")
        if key:
            return str(key)
        html = ctx.http.get_text("https://www.vdab.be/vindeenjob/vacatures")
        b = BUNDLE_RE.search(html)
        k = KEY_RE.search(ctx.http.get_text(b.group(0))) if b else None
        if not k:
            raise ProviderError("vdab needs options.vej_key or GIMME_JOB_VDAB_KEY (could not derive site key)")
        return k.group(1)

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        raw = target.options.get("keywords") or target.query
        if isinstance(raw, str):
            raw = raw.replace("\n", ",").split(",")
        kws = list(dict.fromkeys(str(x).strip() for x in raw or [] if str(x).strip()))
        if not kws:
            raise ProviderError("vdab needs target.query / options.keywords")
        days = int(target.options.get("days") or 30)
        size = min(int(target.options.get("size") or 100), 100)
        headers = {"vej-key-monitor": self._key(target, ctx)}
        jobs: dict[str, Job] = {}
        for kw in kws:
            for page in range(int(target.options.get("max_pages") or 50)):
                data = ctx.http.post_json(API, search_body(kw, days, size, page), headers=headers)
                rows = (data or {}).get("resultaten") or []
                for r in rows:
                    jid = str(((r.get("id") or {}).get("id")) or "")
                    title = ((r.get("vacaturefunctie") or {}).get("naam") or "").strip()
                    if not jid or not title or jid in jobs:
                        continue
                    loc = (r.get("tewerkstellingsLocatieRegioOfAdres") or "").strip()
                    jobs[jid] = self.job(
                        title=title, url=DETAIL_BASE + jid, company=(r.get("vacatureBedrijfsnaam") or "").strip(),
                        location=loc, locations=[loc] if loc else [], country="BE",
                        posted_at=to_iso(r.get("eerstePublicatieDatum")), source_id=jid).validate()
                    if len(jobs) >= ctx.max_jobs:
                        return list(jobs.values())
                if len(rows) < size:
                    break
        return list(jobs.values())


PROVIDER = Vdab()
