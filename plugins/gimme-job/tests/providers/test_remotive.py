import unittest

from tests.providers._helpers import ctx_with
from scripts.providers import _registry
from scripts.providers._base import Target

FIXTURE = {"job-count": 1, "jobs": [
    {"id": 1234, "url": "https://remotive.com/remote-jobs/software-dev/python-dev-1234", "title": "Python Dev",
     "company_name": "Snake Inc", "category": "Software Development", "job_type": "full_time",
     "publication_date": "2026-11-03T14:30:00", "candidate_required_location": "Europe",
     "salary": "$80,000 - $100,000", "description": "<p>Code <i>Python</i>.</p>"},
    {"id": 1, "title": "", "url": "https://remotive.com/x"},
]}


class TestRemotive(unittest.TestCase):
    def setUp(self):
        self.p = _registry.get("remotive")

    def test_detect_none(self):
        self.assertIsNone(self.p.detect("https://remotive.com/"))

    def test_fetch(self):
        jobs = self.p.fetch(Target(query="python"), ctx_with({"remotive.com/api/remote-jobs?search=python": FIXTURE}))
        self.assertEqual(len(jobs), 1)
        j = jobs[0]
        self.assertEqual((j.title, j.company, j.location, j.employment, j.source), ("Python Dev", "Snake Inc", "Europe", "fulltime", "remotive"))
        self.assertEqual((j.salary_min, j.salary_max), (80000, 100000))
        self.assertIn("Python", j.description)
        self.assertTrue(j.posted_at.startswith("2026-11-03"))


if __name__ == "__main__":
    unittest.main()

