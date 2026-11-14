import unittest

from tests.providers._helpers import ctx_with
from scripts.providers import _registry
from scripts.providers._base import Target

FIXTURE = {"totalFound": 2, "content": [
    {"id": "abc-123", "name": "Senior PM", "ref": "https://api.smartrecruiters.com/v1/companies/sgs/postings/abc-123",
     "releasedDate": "2026-10-01T10:00:00.000Z", "location": {"fullLocation": "Geneva, Switzerland", "country": "ch", "remote": False},
     "department": {"label": "Product"}, "typeOfEmployment": {"label": "Full-time"}},
    {"id": "def-456", "name": "Remote AI Engineer", "location": {"city": "Paris", "country": "fr", "remote": True}},
]}


class TestSmartRecruiters(unittest.TestCase):
    def setUp(self):
        self.p = _registry.get("smartrecruiters")

    def test_detect(self):
        self.assertEqual(self.p.detect("https://careers.smartrecruiters.com/SGS").slug, "SGS")
        self.assertEqual(self.p.detect("https://jobs.smartrecruiters.com/SGS/123-x").slug, "SGS")
        self.assertIsNone(self.p.detect("https://example.com/careers"))

    def test_fetch(self):
        ctx = ctx_with({"api.smartrecruiters.com/v1/companies/SGS/postings": FIXTURE})
        jobs = self.p.fetch(Target(company="SGS", slug="SGS"), ctx)
        self.assertEqual(len(jobs), 2)
        self.assertEqual(jobs[0].url, "https://jobs.smartrecruiters.com/SGS/abc-123-senior-pm")
        self.assertEqual((jobs[0].location, jobs[0].department, jobs[0].employment, jobs[0].source), ("Geneva, Switzerland", "Product", "fulltime", "smartrecruiters"))
        self.assertEqual((jobs[1].location, jobs[1].workplace), ("Paris, FR", "remote"))


if __name__ == "__main__":
    unittest.main()

