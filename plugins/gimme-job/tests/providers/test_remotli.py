import unittest

from tests.providers._helpers import ctx_with
from scripts.providers import _registry
from scripts.providers._base import Target

FIXTURE = {"pagination": {"totalPages": 1}, "jobs": [
    {"jobs": {"id": "j1", "status": "active", "title": "Full-Stack Engineer", "slug": "full-stack-engineer-acme",
              "location": "Zurich", "allLocations": ["zurich", "Remote (CH)"],
              "description": "<p>Build <b>things</b></p>", "publishedAt": "2026-11-01T09:00:00Z",
              "salaryMin": 120000, "salaryMax": 150000, "salaryCurrency": "chf"},
     "companies": {"name": "Acme AG"}},
    {"jobs": {"status": "closed", "title": "Old", "slug": "old"}, "companies": {}},
]}


class TestRemotli(unittest.TestCase):
    def test_fetch(self):
        p = _registry.get("remotli")
        jobs = p.fetch(Target(), ctx_with({"remotli.ch/api/jobs": FIXTURE}))
        self.assertEqual(len(jobs), 1)
        j = jobs[0]
        self.assertEqual(j.url, "https://remotli.ch/jobs/full-stack-engineer-acme")
        self.assertEqual((j.company, j.location, j.currency), ("Acme AG", "Zurich; Remote (CH)", "CHF"))
        self.assertEqual(j.description, "Build things")
        self.assertEqual((j.salary_min, j.salary_max), (120000, 150000))


if __name__ == "__main__":
    unittest.main()
