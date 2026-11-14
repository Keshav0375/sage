import unittest

from tests.providers._helpers import ctx_with
from scripts.providers import _registry
from scripts.providers._base import Target

FIXTURE = {"offers": [
    {"id": 11, "title": "Backend Engineer", "status": "published", "careers_url": "https://acme.recruitee.com/o/backend-engineer",
     "city": "Amsterdam", "country": "Netherlands", "remote": True, "published_at": "2026-10-02 09:00:00 UTC",
     "department": "Engineering", "employment_type_code": "fulltime", "description": "<p>Ship it.</p>",
     "salary": {"min": "5000", "max": "7000", "currency": "eur", "period": "month"},
     "locations": [{"name": "Amsterdam HQ", "city": "Amsterdam", "country": "Netherlands"}]},
    {"id": 12, "title": "", "careers_url": "https://acme.recruitee.com/o/x"},
]}


class TestRecruitee(unittest.TestCase):
    def setUp(self):
        self.p = _registry.get("recruitee")

    def test_detect(self):
        self.assertEqual(self.p.detect("https://acme.recruitee.com/").slug, "acme")
        self.assertIsNone(self.p.detect("https://example.com/careers"))
        self.assertIsNone(self.p.detect("https://www.recruitee.com/"))

    def test_fetch(self):
        ctx = ctx_with({"acme.recruitee.com/api/offers": FIXTURE})
        jobs = self.p.fetch(self.p.detect("https://acme.recruitee.com/"), ctx)
        self.assertEqual(len(jobs), 1)
        j = jobs[0]
        self.assertEqual((j.title, j.url, j.workplace, j.source), ("Backend Engineer", "https://acme.recruitee.com/o/backend-engineer", "remote", "recruitee"))
        self.assertEqual(j.location, "Amsterdam HQ, Netherlands")
        self.assertEqual((j.salary_min, j.salary_max, j.currency, j.salary_period), (5000, 7000, "EUR", "month"))
        self.assertIn("Ship it", j.description)


if __name__ == "__main__":
    unittest.main()

