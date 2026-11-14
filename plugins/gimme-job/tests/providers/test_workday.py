import unittest

from tests.providers._helpers import ctx_with
from scripts.providers import _registry
from scripts.providers._base import Target

FIXTURE = {"total": 2, "jobPostings": [
    {"title": "Staff Engineer", "externalPath": "/job/Toronto-ON/Staff-Engineer_JR00123",
     "locationsText": "Toronto, ON", "postedOn": "Posted 3 Days Ago", "bulletFields": ["JR00123"]},
    {"title": "Analyst", "externalPath": "/job/Remote-Canada/Analyst_JR9", "postedOn": "Posted Today", "remoteType": "Fully Remote"},
]}


class TestWorkday(unittest.TestCase):
    def setUp(self):
        self.p = _registry.get("workday")

    def test_detect(self):
        t = self.p.detect("https://acme.wd5.myworkdayjobs.com/en-US/External")
        self.assertEqual(t.api_url, "https://acme.wd5.myworkdayjobs.com/wday/cxs/acme/External/jobs")
        self.assertIsNotNone(self.p.detect("https://wd3.myworkdaysite.com/recruiting/acme/Site"))
        self.assertIsNone(self.p.detect("https://example.com/careers"))

    def test_fetch(self):
        ctx = ctx_with({"/wday/cxs/acme/External/jobs": FIXTURE})
        t = self.p.detect("https://acme.wd5.myworkdayjobs.com/External")
        t.company = "Acme"
        jobs = self.p.fetch(t, ctx)
        self.assertEqual(len(jobs), 2)
        self.assertEqual(jobs[0].url, "https://acme.wd5.myworkdayjobs.com/External/job/Toronto-ON/Staff-Engineer_JR00123")
        self.assertEqual((jobs[0].title, jobs[0].location, jobs[0].source_id, jobs[0].source), ("Staff Engineer", "Toronto, ON", "JR00123", "workday"))
        self.assertEqual(jobs[1].location, "Remote Canada")
        self.assertEqual(jobs[1].workplace, "remote")
        self.assertTrue(jobs[0].posted_at)


if __name__ == "__main__":
    unittest.main()

