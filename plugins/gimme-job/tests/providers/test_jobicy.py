import unittest

from tests.providers._helpers import ctx_with
from scripts.providers import _registry
from scripts.providers._base import Target

FIXTURE = {"jobCount": 1, "hasMore": False, "jobs": [
    {"id": 555, "url": "https://jobicy.com/jobs/555-devops-lead", "jobTitle": "DevOps &amp; SRE Lead",
     "companyName": "Cloudy", "jobGeo": "USA, Canada", "jobType": ["full-time"], "jobIndustry": ["DevOps &amp; Sysadmin"],
     "pubDate": "2026-11-04 09:00:00", "jobDescription": "<p>Keep it up.</p>"},
    {"id": 556, "url": "https://evil.example/x", "jobTitle": "Bad"}]}


class TestJobicy(unittest.TestCase):
    def setUp(self):
        self.p = _registry.get("jobicy")

    def test_detect_none(self):
        self.assertIsNone(self.p.detect("https://jobicy.com/"))

    def test_fetch(self):
        ctx = ctx_with({"jobicy.com/api/v2/remote-jobs?count=100&geo=usa": FIXTURE})
        jobs = self.p.fetch(Target(options={"geo": "usa"}), ctx)
        self.assertEqual(len(jobs), 1)
        j = jobs[0]
        self.assertEqual((j.title, j.company, j.location, j.workplace, j.employment, j.source), ("DevOps & SRE Lead", "Cloudy", "USA, Canada", "remote", "fulltime", "jobicy"))
        self.assertEqual(j.department, "DevOps & Sysadmin")
        self.assertIn("Keep it up", j.description)
        self.assertTrue(j.posted_at.startswith("2026-11-04"))


if __name__ == "__main__":
    unittest.main()

