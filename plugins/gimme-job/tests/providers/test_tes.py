import unittest

from tests.providers._helpers import ctx_with
from scripts.providers import _registry
from scripts.providers._base import Target

FIXTURE = [{"result": {"data": {"json": {"totalPages": 1, "jobs": [
    {"id": 2200123, "title": "Teacher of Maths", "canonicalUrl": "/jobs/vacancy/teacher-of-maths-leeds-2200123",
     "employer": {"name": "Leeds Academy"}, "displayLocation": "Leeds, West Yorkshire",
     "advert": {"startDate": "2026-11-09T09:00:00Z"}, "application": {"closeDate": "2026-12-05T00:00:00Z"},
     "shortDescription": "Great &amp; supportive school", "salary": {"range": "£32,000 - £45,000 per year"}},
    {"id": 1, "title": "Bad", "canonicalUrl": "https://evil.example/x"},
]}}}}]


class TestTes(unittest.TestCase):
    def test_fetch(self):
        p = _registry.get("tes")
        jobs = p.fetch(Target(query="maths"), ctx_with({"tes.com/jobs/api/trpc/jobs.search": FIXTURE}))
        self.assertEqual(len(jobs), 1)
        j = jobs[0]
        self.assertEqual(j.url, "https://www.tes.com/jobs/vacancy/teacher-of-maths-leeds-2200123")
        self.assertEqual((j.company, j.location), ("Leeds Academy", "Leeds, West Yorkshire"))
        self.assertEqual((j.salary_min, j.salary_max, j.currency, j.salary_period), (32000, 45000, "GBP", "year"))
        self.assertEqual(j.description, "Great & supportive school")


if __name__ == "__main__":
    unittest.main()
