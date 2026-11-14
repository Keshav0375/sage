import json
import os
import unittest

from tests.providers._helpers import ctx_with
from scripts.providers import _registry
from scripts.providers._base import ProviderError, Target

FIXTURE = {"results": [{"nbPages": 1, "hits": [
    {"id": "abc123", "objectID": "abc123", "title": "Backend Engineer",
     "company": json.dumps({"name": "Gojek"}), "city": {"name": "Jakarta", "country_name": "Indonesia"},
     "is_remote": True, "published_at": "2026-11-05 08:30:00", "description": "<p>Build <b>APIs</b></p>",
     "external_link": "https://bit.ly/short"},
    {"id": "def456", "title": "Designer", "company": {"name": "Grab"}, "city": {"name": "Singapore"},
     "external_link": "https://grab.example/jobs/1"},
]}]}
OPTS = {"algolia_app": "TESTAPP123", "algolia_key": "k" * 32}


class TestTechInAsia(unittest.TestCase):
    def setUp(self):
        self.p = _registry.get("techinasia")

    def test_fetch(self):
        ctx = ctx_with({"testapp123-dsn.algolia.net/1/indexes/*/queries": FIXTURE})
        jobs = self.p.fetch(Target(options=OPTS), ctx)
        self.assertEqual(len(jobs), 2)
        a, b = jobs
        self.assertEqual(a.url, "https://www.techinasia.com/jobs/abc123")
        self.assertEqual((a.company, a.location, a.workplace), ("Gojek", "Jakarta, Indonesia, Remote", "remote"))
        self.assertEqual(a.description, "Build APIs")
        self.assertEqual(b.url, "https://grab.example/jobs/1")

    def test_needs_credentials(self):
        for k in ("GIMME_JOB_TECHINASIA_ALGOLIA_APP", "GIMME_JOB_TECHINASIA_ALGOLIA_KEY"):
            os.environ.pop(k, None)
        with self.assertRaises(ProviderError):
            self.p.fetch(Target(), ctx_with({}))


if __name__ == "__main__":
    unittest.main()
