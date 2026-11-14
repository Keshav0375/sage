"""Test helpers: a Context whose HTTP layer serves canned responses (no network)."""
from scripts.providers._base import Context
from scripts.providers._http import FakeTransport, Http


def ctx_with(routes: dict, max_jobs: int = 500) -> Context:
    """routes: {url_substring: dict|list (JSON) | str (text) | (status, body) | Response}."""
    return Context(http=Http(FakeTransport(routes), retries=1), max_jobs=max_jobs)
