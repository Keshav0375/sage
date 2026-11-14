import unittest

from tests.providers._helpers import ctx_with
from scripts.providers import _registry
from scripts.providers._base import Target

RESP = {"refineSearch": {"totalHits": 1, "data": {"jobs": [
    {"jobId": "JR100", "title": "Sr. M&amp;A Analyst", "location": "London, England, United Kingdom",
     "postedDate": "2026-11-02T00:00:00.000+0000", "category": "Finance"}]}}}


class TestPhenom(unittest.TestCase):
    def test_fetch(self):
        p = _registry.get("phenom")
        ctx = ctx_with({"careers.acme.com/widgets": RESP})
        jobs = p.fetch(Target(company="Acme", careers_url="https://careers.acme.com/global/en/search-results"), ctx)
        self.assertEqual(len(jobs), 1)
        j = jobs[0]
        self.assertEqual((j.title, j.location, j.department, j.source), ("Sr. M&A Analyst", "London, England, United Kingdom", "Finance", "phenom"))
        self.assertEqual(j.url, "https://careers.acme.com/global/en/job/JR100/Sr-M-A-Analyst")
        self.assertTrue(j.posted_at.startswith("2026-11-02"))

    def test_detect_is_none(self):
        self.assertIsNone(_registry.get("phenom").detect("https://careers.acme.com/"))


if __name__ == "__main__":
    unittest.main()
