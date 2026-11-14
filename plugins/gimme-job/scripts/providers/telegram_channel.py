"""Telegram public channels — the server-rendered preview at t.me/s/<channel> (no login, no API).

Channel handle from ``Target.options['channel']`` (or the last path segment of careers_url like https://t.me/s/<channel>).
A post becomes a Job only when it names an employer AND links to a vacancy page; everything else is dropped
(a wrong employer is worse than a missing row). Pages back with ?before=<id>, stopping at ``since_days`` (default 30).

SIMPLIFIED vs career-ops providers/telegram-channel.mjs (MIT): we keep the four main employer shapes
(labelled "Company:" line, "Title @ Employer", "Title | Employer", second line "в/at Employer") and the
hashtag-first-line template; the Russian-language positional heuristics (sector/department/person filters,
"Employer ищет", salary-line employer) are not ported. Code is our own.
"""
from __future__ import annotations

import html as _html
import re
from datetime import datetime, timedelta, timezone
from urllib.parse import parse_qs, urlsplit

from ._base import Context, Job, Provider, ProviderError, Target
from ._parse import html_to_text, to_iso

CHANNEL_RE = re.compile(r"^[a-z0-9_]{5,32}$", re.I)
TITLE_CAP = 120
DESC_CAP = 4000
L = r"[^\W\d_]"  # a letter

NON_APPLY = re.compile(r"(^|\.)(t\.me|telegram\.me|telegram\.org|telegra\.ph|vk\.com|vk\.cc|ok\.ru|facebook\.com|fb\.com|instagram\.com|youtube\.com|youtu\.be|x\.com|twitter\.com|tiktok\.com|threads\.net|play\.google\.com|apps\.apple\.com|substack\.com|medium\.com|habr\.com|github\.com)$", re.I)
SHORTENER = re.compile(r"(^|\.)(goo\.gl|bit\.ly|t\.co|clck\.ru|tinyurl\.com|cutt\.ly|is\.gd|ow\.ly|rb\.gy)$", re.I)
FORM = re.compile(r"(^|\.)(forms\.gle|docs\.google\.com|typeform\.com|tally\.so|airtable\.com|notion\.site|notion\.so)$", re.I)
BOARD = re.compile(r"(^|\.)(getmatch\.ru|finder\.work|geekjob\.ru|linkedin\.com|hh\.ru|career\.habr\.com|djinni\.co|indeed\.com|glassdoor\.com|weworkremotely\.com|remoteok\.com|arbeitnow\.com|cryptojobslist\.com|relocate\.me)$", re.I)
VACANCY = re.compile(r"/(vacanc|job|position|opening|career|apply|hiring)|[-_/](?!(?:19|20)\d{2}(?=[/?#]|$))\d{4,}(?=[/?#]|$)|[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", re.I)
TRACKING = re.compile(r"^(utm_|ref$|referrer$|source$|src$|s$|from$|campaign$|fbclid$|gclid$|yclid$|mc_|_hs|igshid$|trk$)", re.I)
LISTING_ROOT = re.compile(r"^/(jobs|vacancies|careers|career|vacancy|vakansii|job)$", re.I)
LOCALE_ROOT = re.compile(r"^(/[a-z]{2}(-[a-z]{2})?)?$", re.I)

LABEL = re.compile(rf"^[^\w]{{0,3}}\s*(?:компания|компанія|company|работодатель|employer|hiring company)\s*[:：]\s*(.{{2,80}})$", re.I)
LOCATIONISH = re.compile(r"\b(remote|hybrid|onsite|office|full[- ]?time|part[- ]?time|berlin|london|germany|europe|usa)\b", re.I)
ANON = re.compile(r"(?:название скрыто|компания скрыта|name hidden|undisclosed|confidential|\bour client\b)", re.I)
DATE_LIKE = re.compile(r"\b(19|20)\d{2}\b|\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*\b", re.I)
HASHTAGS = re.compile(r"^#\S+(?:\s+#\S+)*$")
ROLE_WORD = re.compile(r"(?<!\w)(senior|middle|junior|lead|principal|staff|head|chief|intern|trainee|engineer|developer|manager|analyst|designer|architect|specialist|consultant|director|recruiter|scientist|product\s+owner|qa|tester|devops|sre|инженер|разработчик|менеджер|специалист|аналитик|директор|архитектор)(?!\w)", re.I)
FORMAT_ONLY = re.compile(r"^(?:(?:worldwide|anywhere|global|remote|hybrid|on-?site|office|relocation|full[- ]?time|part[- ]?time|удал[её]нн?\w*|гибрид\w*|офис\w*|релокац\w*)(?!\w)[\s,/()·|-]*)+$", re.I)
ZW = re.compile("[​-‍﻿]")


def _plausible(name: str, from_title: bool) -> str:
    n = ZW.sub("", name).strip()
    if not 2 <= len(n) <= 60 or len(n.split()) > 4:
        return ""
    if re.search(r"[,:;!?]", n) or n.endswith("."):
        return ""
    if LOCATIONISH.search(n) or ANON.search(n):
        return ""
    if from_title and (DATE_LIKE.search(n) or re.search(r"\d", n)):
        return ""
    if not re.search(r"[A-ZА-ЯЁ]", n):
        return ""
    if FORMAT_ONLY.match(re.sub(r"[\W_]+$", "", n)):
        return ""
    return n


def employer_name(lines: list[str]) -> str:
    for line in lines[:40]:
        m = LABEL.match(line)
        if m:
            return _plausible(re.sub(r"\s*[|(].*$", "", m.group(1)), False)
    first = lines[0] if lines else ""
    second = lines[1] if len(lines) > 1 else ""
    m = re.match(r"^.{3,140}?\s+@\s+(.{2,60})$", first)
    if m:
        return _plausible(m.group(1), True)
    if not re.search(r"\|.*\|", first):
        m = re.match(r"^.{3,140}?\s+\|\s+([^|]{2,60})$", first)
        if m:
            e = _plausible(m.group(1), True)
            if e and not re.fullmatch(ROLE_WORD.pattern, e, re.I):
                return e
    m = re.match(r"^(?:в|at)\s+([^—–,(]{2,60}?)\s*(?:[—–]|$)", second)
    if m:
        return _plausible(m.group(1), True)
    if HASHTAGS.match(first) and second:
        e = _plausible(second, False)
        if e and not ROLE_WORD.search(e):
            return e
    return ""


def classify_link(href: str):
    p = urlsplit(href or "")
    if p.scheme != "https" or not p.hostname:
        return None
    host = re.sub(r"^www\.", "", p.hostname.lower())
    board = bool(BOARD.search(host))
    if (not board and NON_APPLY.search(host)) or SHORTENER.search(host) or FORM.search(host):
        return None
    path = p.path.rstrip("/")
    if host.endswith("linkedin.com"):
        return "board" if "/jobs/view/" in path else None
    if host == "career.habr.com":
        return "board" if re.fullmatch(r"/vacancies/\d+", path) else None
    identifying = any(not TRACKING.match(k) for k in parse_qs(p.query))
    if (LOCALE_ROOT.match(path) or LISTING_ROOT.match(path)) and not identifying:
        return None
    if not VACANCY.search(path) and not identifying:
        return None
    return "board" if board else "employer"


def _vacancy_key(href: str) -> str:
    p = urlsplit(href)
    keep = sorted((k, tuple(v)) for k, v in parse_qs(p.query).items() if not TRACKING.match(k))
    return f"{re.sub(r'^www[.]', '', (p.hostname or '').lower())}{p.path.rstrip('/')}?{keep}"


def application_link(hrefs: list[str]):
    seen, qualified = set(), []
    for h in hrefs:
        kind = classify_link(h)
        if not kind or _vacancy_key(h) in seen:
            continue
        seen.add(_vacancy_key(h))
        qualified.append((h, kind))
    if not qualified:
        return None
    for kind in ("employer", "board"):
        if sum(1 for _, k in qualified if k == kind) > 1:
            return None  # a digest of several vacancies
    return next((q for q in qualified if q[1] == "employer"), qualified[0])


def _headline(line: str) -> str:
    if len(line) <= TITLE_CAP:
        return line
    cut = line[:TITLE_CAP]
    sp = cut.rfind(" ")
    return (cut[:sp] if sp > TITLE_CAP / 3 else cut) + "…"


def parse_channel_page(page: str, channel: str):
    chunks = (page or "").split('<div class="tgme_widget_message_wrap')[1:]
    posts, seen = [], set()
    for chunk in chunks:
        if re.search(r"\bservice_message\b", chunk):
            continue
        m = re.search(r'data-post="([^"/]+)/(\d+)"', chunk)
        if not m or m.group(1).lower() != channel.lower():
            continue
        pid = int(m.group(2))
        tm = re.search(r'class="tgme_widget_message_text[^"]*"[^>]*>(.*?)</div>', chunk, re.S)
        if pid in seen or not tm:
            continue
        lines = [ZW.sub("", html_to_text(l)) for l in re.split(r"<br\s*/?>", tm.group(1), flags=re.I)]
        lines = [l for l in lines if l]
        if not lines:
            continue
        hrefs = [_html.unescape(_html.unescape(h)) for h in re.findall(r'href="([^"]+)"', tm.group(1))]
        dt = re.search(r'<time datetime="([^"]+)"', chunk)
        seen.add(pid)
        posts.append({"id": pid, "url": f"https://t.me/{channel}/{pid}", "title": _headline(lines[0]),
                      "description": "\n".join(lines), "lines": lines, "hrefs": hrefs,
                      "posted": to_iso(dt.group(1)) if dt else ""})
    no_preview = not posts and bool(re.search(r'<meta property="og:title" content="Telegram: Contact @', page or "", re.I))
    return posts, no_preview


class TelegramChannel(Provider):
    name = "telegram-channel"
    wave = "W3"
    kind = "feed"
    tenant = True
    hosts = ("t.me",)

    def detect(self, careers_url: str):
        p = urlsplit(careers_url or "")
        if p.netloc.lower() == "t.me":
            parts = [x for x in p.path.split("/") if x]
            if parts and parts[0] == "s":
                parts = parts[1:]
            if parts and CHANNEL_RE.match(parts[0]):
                return Target(careers_url=careers_url, options={"channel": parts[0]})
        return None

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        channel = str(target.options.get("channel") or (self.detect(target.careers_url) or Target()).options.get("channel") or "")
        channel = channel.lstrip("@").strip()
        if not CHANNEL_RE.match(channel):
            raise ProviderError("telegram-channel needs options.channel (5-32 letters, digits, underscores)")
        max_pages = min(int(target.options.get("max_pages") or 10), 10)
        days = float(target.options.get("since_days") or 30)
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        jobs: list[Job] = []
        before = None
        for page in range(max_pages):
            url = f"https://t.me/s/{channel}" + (f"?before={before}" if before is not None else "")
            posts, no_preview = parse_channel_page(ctx.http.get_text(url), channel)
            if page == 0 and no_preview:
                raise ProviderError(f"telegram-channel: @{channel} has no public preview")
            if not posts:
                break
            oldest = min(p["id"] for p in posts)
            if before is not None and oldest >= before:
                break
            reached = False
            for p in posts:
                if p["posted"] and p["posted"] < cutoff:
                    reached = True
                    continue
                job = self._to_job(p)
                if job:
                    jobs.append(job)
                    if len(jobs) >= ctx.max_jobs:
                        return jobs
            if reached:
                break
            before = oldest
        return jobs

    def _to_job(self, p) -> Job | None:
        lines = p["lines"]
        company = employer_name(lines)
        if not company or ANON.search("\n".join(lines[:3])):
            return None
        link = application_link(p["hrefs"])
        if not link:
            return None
        title = p["title"]
        if HASHTAGS.match(lines[0]):
            better = next((l for l in lines[1:] if l.lower() != company.lower() and employer_name(["", l]).lower() != company.lower()
                           and not HASHTAGS.match(l) and not re.match(r"https?://", l) and l not in p["hrefs"]
                           and not FORMAT_ONLY.match(l)), None)
            if not better:
                return None
            title = _headline(better)
        elif re.search(r"https?://\S+$", lines[0]):
            title = _headline(re.sub(r"\s*[:—–-]?\s*https?://\S+$", "", lines[0])) or title
        src = f"\n\nSource: {p['url']}"
        return self.job(title=title, url=link[0], company=company,
                        description=p["description"][: DESC_CAP - len(src)] + src,
                        posted_at=p["posted"], source_id=str(p["id"]), extra={"telegram_post": p["url"]}).validate()


PROVIDER = TelegramChannel()
