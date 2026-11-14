import json
import unittest

from tests.providers._helpers import ctx_with
from scripts.providers import _registry
from scripts.providers._base import Target

FIXTURE = {"jobs": [
    {"id": 5, "title": "Product Designer", "slug": "product-designer-acme", "company_name": "Acme",
     "work_arrangement": "remote", "locations": [{"city": "Lisbon", "country": "Portugal"}], "posted": 1793000000},
    {"id": 6, "title": "Old", "slug": "old-job", "company_name": "Z", "is_expired": True}], "total": 2, "page": 1, "has_more": False}


class TestFourDayWeek(unittest.TestCase):
    def test_fetch(self):
        p = _registry.get("4dayweek")
        jobs = p.fetch(Target(), ctx_with({"4dayweek.io/api/jobs": FIXTURE}))
        self.assertEqual(len(jobs), 1)
        j = jobs[0]
        self.assertEqual((j.title, j.company, j.location), ("Product Designer", "Acme", "Lisbon, Portugal, Remote"))
        self.assertEqual(j.url, "https://4dayweek.io/job/product-designer-acme")
        self.assertEqual((j.source, j.workplace), ("4dayweek", "remote"))
        self.assertTrue(j.posted_at.startswith("2026-"))


if __name__ == "__main__":
    unittest.main()
