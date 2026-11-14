"""HTTP layer for scanners: stdlib urllib, robots.txt, crawl delay, retry with backoff, body cap.

Tests swap the transport with ``FakeTransport`` so no scanner test touches the network.
"""
from __future__ import annotations

import json
import random
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
from typing import Any, Callable, Optional

from ._base import ProviderError

USER_AGENT = "gimme-job/0.1 (+personal job search; respects robots.txt)"
MAX_BODY = 8 * 1024 * 1024
RETRY_STATUS = {429, 500, 502, 503, 504}


class Response:
    def __init__(self, status: int, body: bytes, headers: Optional[dict[str, str]] = None, url: str = ""):
        self.status = status
        self.body = body
        self.headers = {k.lower(): v for k, v in (headers or {}).items()}
        self.url = url

    @property
    def text(self) -> str:
        return self.body.decode("utf-8", errors="replace")

    def json(self) -> Any:
        try:
            return json.loads(self.text)
        except json.JSONDecodeError as e:
            raise ProviderError(f"bad JSON from {self.url}: {e}") from e


class UrllibTransport:
    def request(self, method: str, url: str, headers: dict[str, str], data: Optional[bytes], timeout: float) -> Response:
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                body = r.read(MAX_BODY + 1)
                if len(body) > MAX_BODY:
                    raise ProviderError(f"body over {MAX_BODY} bytes: {url}")
                return Response(r.status, body, dict(r.headers), r.geturl())
        except urllib.error.HTTPError as e:
            return Response(e.code, e.read(65536) if e.fp else b"", dict(e.headers or {}), url)


class FakeTransport:
    """Maps URL substrings (or callables) to canned responses. First match wins."""

    def __init__(self, routes: Optional[dict[str, Any]] = None):
        self.routes: list[tuple[Any, Any]] = list((routes or {}).items())
        self.calls: list[tuple[str, str, Optional[bytes]]] = []

    def add(self, match: Any, response: Any) -> "FakeTransport":
        self.routes.append((match, response))
        return self

    def request(self, method, url, headers, data, timeout) -> Response:
        self.calls.append((method, url, data))
        for match, resp in self.routes:
            hit = match(url) if callable(match) else match in url
            if not hit:
                continue
            if isinstance(resp, Response):
                return resp
            if isinstance(resp, (dict, list)):
                return Response(200, json.dumps(resp).encode(), {"content-type": "application/json"}, url)
            if isinstance(resp, tuple):
                status, body = resp
                return Response(status, body.encode() if isinstance(body, str) else body, {}, url)
            return Response(200, resp.encode() if isinstance(resp, str) else resp, {}, url)
        return Response(404, b"not found (FakeTransport)", {}, url)


class Http:
    def __init__(self, transport: Any = None, *, timeout: float = 20.0, retries: int = 4,
                 min_delay: float = 1.0, respect_robots: bool = True, sleep: Callable[[float], None] = time.sleep,
                 on_call: Optional[Callable[[dict], None]] = None):
        self.transport = transport or UrllibTransport()
        self.timeout = timeout
        self.retries = retries
        self.min_delay = min_delay
        self.respect_robots = respect_robots and isinstance(self.transport, UrllibTransport)
        self.sleep = sleep if isinstance(self.transport, UrllibTransport) else (lambda s: None)
        self.on_call = on_call
        self._last: dict[str, float] = {}
        self._robots: dict[str, Optional[urllib.robotparser.RobotFileParser]] = {}
        self._delay: dict[str, float] = {}
        self._lock = threading.Lock()

    # ---- robots + politeness -------------------------------------------------
    def _robots_for(self, url: str) -> Optional[urllib.robotparser.RobotFileParser]:
        p = urllib.parse.urlsplit(url)
        base = f"{p.scheme}://{p.netloc}"
        if base not in self._robots:
            rp = urllib.robotparser.RobotFileParser()
            try:
                r = self.transport.request("GET", base + "/robots.txt", {"User-Agent": USER_AGENT}, None, 10)
                if r.status == 200:
                    rp.parse(r.text.splitlines())
                    delay = rp.crawl_delay(USER_AGENT)
                    if delay:
                        self._delay[p.netloc] = float(delay)
                else:
                    rp = None
            except Exception:
                rp = None
            self._robots[base] = rp
        return self._robots[base]

    def allowed(self, url: str) -> bool:
        if not self.respect_robots:
            return True
        rp = self._robots_for(url)
        return True if rp is None else rp.can_fetch(USER_AGENT, url)

    def _wait_turn(self, host: str) -> None:
        with self._lock:
            gap = max(self.min_delay, self._delay.get(host, 0.0))
            now = time.monotonic()
            wait = self._last.get(host, 0.0) + gap - now
            self._last[host] = max(now, self._last.get(host, 0.0) + gap)
        if wait > 0:
            self.sleep(wait)

    # ---- requests ------------------------------------------------------------
    def request(self, method: str, url: str, *, headers: Optional[dict[str, str]] = None,
                data: Any = None, ok: tuple[int, ...] = (200,)) -> Response:
        if not url.startswith(("http://", "https://")):
            raise ProviderError(f"refusing non-http url: {url}")
        if not self.allowed(url):
            self._record(url, method, "blocked", "robots.txt disallows")
            raise ProviderError(f"robots.txt disallows {url}")
        h = {"User-Agent": USER_AGENT, "Accept": "application/json, text/html;q=0.9, */*;q=0.5"}
        h.update(headers or {})
        body = None
        if data is not None:
            if isinstance(data, (dict, list)):
                body = json.dumps(data).encode()
                h.setdefault("Content-Type", "application/json")
            elif isinstance(data, str):
                body = data.encode()
            else:
                body = data
        host = urllib.parse.urlsplit(url).netloc
        last_err = ""
        for attempt in range(self.retries):
            self._wait_turn(host)
            try:
                r = self.transport.request(method, url, h, body, self.timeout)
            except ProviderError:
                raise
            except Exception as e:  # network error
                last_err = f"{type(e).__name__}: {e}"
                self.sleep(min(30, 2 ** attempt + random.random()))
                continue
            if r.status in ok:
                self._record(url, method, "ok", str(r.status))
                return r
            last_err = f"HTTP {r.status}"
            if r.status not in RETRY_STATUS:
                break
            retry_after = r.headers.get("retry-after", "")
            self.sleep(float(retry_after) if retry_after.isdigit() else min(30, 2 ** attempt + random.random()))
        self._record(url, method, "failed", last_err)
        raise ProviderError(f"{method} {url} failed: {last_err}")

    def get(self, url: str, **kw: Any) -> Response:
        return self.request("GET", url, **kw)

    def post(self, url: str, data: Any = None, **kw: Any) -> Response:
        return self.request("POST", url, data=data, **kw)

    def get_json(self, url: str, **kw: Any) -> Any:
        return self.get(url, **kw).json()

    def post_json(self, url: str, data: Any = None, **kw: Any) -> Any:
        return self.post(url, data=data, **kw).json()

    def get_text(self, url: str, **kw: Any) -> str:
        return self.get(url, **kw).text

    def _record(self, url: str, method: str, status: str, detail: str) -> None:
        if self.on_call:
            self.on_call({"tool": "http", "host": urllib.parse.urlsplit(url).netloc, "method": method,
                          "status": status, "detail": detail, "ts": time.time()})
