import unittest

from tests.providers._helpers import ctx_with
from scripts.providers import _registry
from scripts.providers._base import Target

PORTAL = '<html><script id="__NEXT_DATA__" type="application/json">{"props":{"pageProps":{"network":{"id":"4242"}}}}</script></html>'
RESULT = {"results": {"count": 1, "jobs": [
    {"id": 77, "title": "ML Engineer", "url": "https://jobs.example.vc/companies/orbit/jobs/77-ml", "created_at": 1762000000,
     "organization": {"name": "Orbit"}, "locations": ["Toronto, ON, Canada"], "work_mode": "remote",
     "compensation_amount_min_cents": 12000000, "compensation_amount_max_cents": 16000000,
     "compensation_currency": "USD", "compensation_period": "year"}]}}


class TestGetro(unittest.TestCase):
    def setUp(self):
        self.p = _registry.get("getro")

    def test_detect(self):
        self.assertEqual(self.p.detect("https://api.getro.com/api/v2/collections/4242/search/jobs").options["collection"], "4242")
        self.assertIsNotNone(self.p.detect("https://example.getro.com/jobs"))
        self.assertIsNone(self.p.detect("https://example.com/careers"))

    def test_fetch_resolves_collection(self):
        ctx = ctx_with({"collections/4242/search/jobs": RESULT, "jobs.example.vc": PORTAL})
        jobs = self.p.fetch(Target(company="Example VC", careers_url="https://jobs.example.vc/jobs", options={"max_age_days": 0}), ctx)
        self.assertEqual(len(jobs), 1)
        j = jobs[0]
        self.assertEqual((j.title, j.company, j.location, j.workplace, j.source), ("ML Engineer", "Orbit", "Toronto, ON, Canada, Remote", "remote", "getro"))
        self.assertEqual((j.salary_min, j.salary_max, j.currency), (120000, 160000, "USD"))


if __name__ == "__main__":
    unittest.main()

