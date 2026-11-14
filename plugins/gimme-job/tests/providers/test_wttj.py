import os
import unittest

from tests.providers._helpers import ctx_with
from scripts.providers import _registry
from scripts.providers._base import ProviderError, Target

FIXTURE = {"hits": [{
    "objectID": "o1", "name": "Data Scientist", "slug": "data-scientist_paris",
    "organization": {"name": "Acme SAS", "slug": "acme-sas"},
    "offices": [{"city": "Paris", "country": "France"}], "remote": "fulltime",
    "published_at_timestamp": 1762732800, "salary_yearly_minimum": 55000, "salary_maximum": 70000,
    "salary_period": "yearly", "salary_currency": "eur",
}, {"name": "Bad", "slug": "bad slug", "organization": {"slug": "x"}}]}
OPTS = {"algolia_app": "TESTAPP123", "algolia_key": "k" * 32}


class TestWttj(unittest.TestCase):
    def setUp(self):
        self.p = _registry.get("wttj")

    def test_fetch(self):
        ctx = ctx_with({"testapp123-dsn.algolia.net/1/indexes/wttj_jobs_production_en/query": FIXTURE})
        jobs = self.p.fetch(Target(query="data", options=OPTS), ctx)
        self.assertEqual(len(jobs), 1)
        j = jobs[0]
        self.assertEqual(j.url, "https://www.welcometothejungle.com/en/companies/acme-sas/jobs/data-scientist_paris")
        self.assertEqual((j.company, j.location, j.currency), ("Acme SAS", "Paris, France, Remote", "EUR"))
        self.assertEqual((j.salary_min, j.salary_max), (55000, 70000))
        self.assertTrue(j.posted_at.startswith("2025-11-10"))

    def test_needs_credentials(self):
        for k in ("GIMME_JOB_WTTJ_ALGOLIA_APP", "GIMME_JOB_WTTJ_ALGOLIA_KEY"):
            os.environ.pop(k, None)
        with self.assertRaises(ProviderError):
            self.p.fetch(Target(query="x"), ctx_with({}))


if __name__ == "__main__":
    unittest.main()
