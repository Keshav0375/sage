import unittest

from tests.providers._helpers import ctx_with
from scripts.providers import _registry
from scripts.providers._base import Target

PAGE1 = {"jobs": [
    {"title": "Data Scientist", "companyName": "Orbit", "applicationLink": "https://himalayas.app/companies/orbit/jobs/ds-1",
     "guid": "https://himalayas.app/companies/orbit/jobs/ds-1", "locationRestrictions": ["Canada", "United States"],
     "pubDate": 1762000000, "employmentType": "Full Time", "minSalary": 100000, "maxSalary": 130000, "salaryCurrency": "USD"}],
    "nextCursor": "c2"}
PAGE2 = {"jobs": [
    {"title": "Writer", "companyName": "Ink", "applicationLink": "https://evil.example/x", "guid": "https://himalayas.app/companies/ink/jobs/w-1",
     "locationRestrictions": [], "pubDate": "2026-11-01T00:00:00Z"}]}


class TestHimalayas(unittest.TestCase):
    def setUp(self):
        self.p = _registry.get("himalayas")

    def test_detect_none(self):
        self.assertIsNone(self.p.detect("https://himalayas.app/"))

    def test_fetch_paginates(self):
        ctx = ctx_with({"cursor=c2": PAGE2, "himalayas.app/jobs/api": PAGE1})
        jobs = self.p.fetch(Target(), ctx)
        self.assertEqual(len(jobs), 2)
        a, b = jobs
        self.assertEqual((a.title, a.company, a.location, a.employment, a.source), ("Data Scientist", "Orbit", "Canada, United States", "fulltime", "himalayas"))
        self.assertEqual((a.salary_min, a.currency), (100000, "USD"))
        self.assertEqual((b.url, b.location), ("https://himalayas.app/companies/ink/jobs/w-1", "Remote (worldwide)"))


if __name__ == "__main__":
    unittest.main()

