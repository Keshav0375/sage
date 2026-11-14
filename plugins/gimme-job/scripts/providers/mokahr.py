"""MokaHR — POST {origin}/api/outer/ats-apply/website/jobs/v2 (tenant careers sites).

Mechanism from career-ops providers/mokahr.mjs (MIT); code is our own.
hire-r1.mokahr.com answers with plain JSON; app.mokahr.com answers with an AES-128-CBC
{data, necromancer} envelope, which we decrypt through the system ``openssl`` CLI (stdlib has no AES).
"""
from __future__ import annotations

import base64
import json
import re
import subprocess
from urllib.parse import quote, urlsplit

from ._base import Context, Job, Provider, ProviderError, Target
from ._parse import html_to_text, to_iso

API_PATH = "/api/outer/ats-apply/website/jobs/v2"
HOSTS = ("app.mokahr.com", "hire-r1.mokahr.com")
IV = b"de7c21ed8d6f50fe"
LIMIT = 50
TENANT_RE = re.compile(r"^/(?:social-recruitment|campus-recruitment|apply)/([^/]+)/(\d+)/?$")


def _tenant(url: str):
    p = urlsplit(url or "")
    if p.scheme != "https" or p.netloc.lower() not in HOSTS:
        return None
    m = TENANT_RE.match(p.path)
    if not m or int(m.group(2)) <= 0:
        return None
    return m.group(1), int(m.group(2)), f"https://{p.netloc}{p.path.rstrip('/')}", f"https://{p.netloc}{API_PATH}"


def decrypt_envelope(env: dict):
    if not env.get("data") or not env.get("necromancer"):
        raise ProviderError("mokahr: response missing data/necromancer")
    key = env["necromancer"].encode()
    if len(key) != 16:
        raise ProviderError("mokahr: necromancer key must be 16 bytes")
    try:
        r = subprocess.run(["openssl", "enc", "-d", "-aes-128-cbc", "-K", key.hex(), "-iv", IV.hex()],
                           input=base64.b64decode(env["data"]), capture_output=True, timeout=20)
    except (OSError, subprocess.SubprocessError) as e:
        raise ProviderError(f"mokahr: cannot decrypt envelope (needs openssl): {e}") from e
    if r.returncode != 0:
        raise ProviderError("mokahr: envelope decryption failed")
    return json.loads(r.stdout.decode("utf-8"))


class MokaHr(Provider):
    name = "mokahr"
    wave = "W6"
    kind = "ats"
    tenant = True
    hosts = HOSTS

    def detect(self, careers_url: str):
        t = _tenant(careers_url)
        if not t:
            return None
        return Target(slug=t[0], careers_url=careers_url, api_url=t[3], options={"site_id": t[1]})

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        t = _tenant(target.careers_url)
        if not t:
            raise ProviderError("mokahr: careers_url must be a mokahr tenant URL with a site id")
        org, site_id, base, api = t
        jobs: list[Job] = []
        seen: set[str] = set()
        offset = 0
        while len(jobs) < ctx.max_jobs:
            body = {"siteId": site_id, "orgId": org, "locale": "zh-CN", "limit": LIMIT, "offset": offset}
            if target.query:
                body["keyword"] = target.query
            env = ctx.http.post_json(api, body)
            data = env.get("data") if isinstance(env, dict) else None
            plain = env if isinstance(data, dict) else decrypt_envelope(env or {})
            if plain.get("success") is False:
                raise ProviderError(f"mokahr: API error {plain.get('msg') or plain.get('code')}")
            rows = (plain.get("data") or {}).get("jobs")
            if not isinstance(rows, list) or not rows:
                break
            for j in rows:
                jid = j.get("id")
                if not j.get("title") or jid is None or str(jid) in seen:
                    continue
                seen.add(str(jid))
                locs = [" ".join(x for x in [l.get("provinceName"), l.get("cityName")] if x)
                        for l in j.get("locations") or []]
                created = str(j.get("createdAt") or "").strip()
                desc = html_to_text(j.get("jobDescription") or "")
                jobs.append(self.job(
                    title=j["title"], url=f"{base}#/job/{quote(str(jid), safe='')}",
                    company=target.company or org, locations=[x for x in locs if x],
                    department=(j.get("department") or {}).get("name", ""),
                    posted_at=to_iso(created) if re.search(r"(Z|[+-]\d{2}:\d{2})$", created, re.I) else "",
                    description=desc[:4000], source_id=str(jid)).validate())
            if len(rows) < LIMIT:
                break
            offset += LIMIT
        return jobs[: ctx.max_jobs]


PROVIDER = MokaHr()
