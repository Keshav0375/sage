import unittest

from tests.providers._helpers import ctx_with
from scripts.providers import _registry
from scripts.providers._base import Target

RESP = {"totalCount": 1, "count": 1, "jobs": [{"data": {"slug": "12345", "req_id": "12345", "title": "Pharmacist",
        "hiring_organization": "Acme Health", "full_location": "Boise, ID, United States", "category": "Pharmacy"}}]}
URL = "https://acme.jibeapply.com/main/jobs"


class TestJibeApply(unittest.TestCase):
    def setUp(self):
        self.p = _registry.get("jibeapply")

    def test_detect(self):
        t = self.p.detect(URL)
        self.assertEqual(t.api_url, "https://acme.jibeapply.com/api/main/jobs")
        self.assertIsNone(self.p.detect("https://example.com/careers"))

    def test_fetch(self):
        jobs = self.p.fetch(Target(company="Acme", careers_url=URL), ctx_with({"acme.jibeapply.com/api/main/jobs": RESP}))
        self.assertEqual(len(jobs), 1)
        j = jobs[0]
        self.assertEqual((j.title, j.company, j.location, j.department, j.source), ("Pharmacist", "Acme Health", "Boise, ID, United States", "Pharmacy", "jibeapply"))
        self.assertEqual(j.url, "https://acme.jibeapply.com/jobs/12345")


if __name__ == "__main__":
    unittest.main()
