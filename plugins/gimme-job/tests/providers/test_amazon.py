import json
import unittest

from tests.providers._helpers import ctx_with
from scripts.providers import _registry
from scripts.providers._base import Target

FIXTURE = {"hits": 1, "jobs": [{
    "id_icims": "3012345", "title": "Software Development Engineer", "job_path": "/en/jobs/3012345/software-development-engineer",
    "company_name": "Amazon.com Services LLC", "normalized_location": "Seattle, Washington, USA", "location": "US, WA, Seattle",
    "locations": ['{"location":"US, VA, Arlington","normalizedLocation":"Arlington, Virginia, USA"}'],
    "posted_date": "November  3, 2026", "job_category": "Software Development"}]}


class TestAmazon(unittest.TestCase):
    def test_detect(self):
        p = _registry.get("amazon")
        self.assertIsNotNone(p.detect("https://www.amazon.jobs/en/"))
        self.assertIsNone(p.detect("https://example.com"))

    def test_fetch(self):
        ctx = ctx_with({"amazon.jobs/en/search.json": FIXTURE})
        jobs = _registry.get("amazon").fetch(Target(query="sde"), ctx)
        self.assertEqual(len(jobs), 1)
        j = jobs[0]
        self.assertEqual(j.title, "Software Development Engineer")
        self.assertEqual(j.url, "https://www.amazon.jobs/en/jobs/3012345/software-development-engineer")
        self.assertEqual(j.location, "Seattle, Washington, USA · Arlington, Virginia, USA")
        self.assertEqual(j.posted_at, "2026-11-03")
        self.assertIn("base_query=sde", ctx.http.transport.calls[0][1])


if __name__ == "__main__":
    unittest.main()
