import unittest

from tests.providers._helpers import ctx_with
from scripts.providers import _registry
from scripts.providers._base import Target

FIXTURE = {"status": "success", "job_counts": 1, "data": [{
    "id": "a1b2c3", "title": "Product Manager", "internal_job_code": "PM-7",
    "locations": "Multiple Locations", "tool_tip_locations": ["Mumbai , India", "Pune , India"],
    "posted_on": 1760000000, "jd": "<p>Own the <b>roadmap</b></p>",
    "salary_timeframe": "Annual", "salary_min": "1500000", "salary_max": "2500000", "salary_currency": "inr",
}]}
URL = "https://acme.darwinbox.in/ms/candidatev2/abc123/careers/allJobs"


class TestDarwinbox(unittest.TestCase):
    def setUp(self):
        self.p = _registry.get("darwinbox")

    def test_detect(self):
        self.assertEqual(self.p.detect(URL).slug, "abc123")
        self.assertIsNone(self.p.detect("https://acme.darwinbox.in/"))
        self.assertIsNone(self.p.detect("https://example.com/ms/candidatev2/abc/careers"))

    def test_fetch(self):
        ctx = ctx_with({"acme.darwinbox.in/ms/candidateapi/job/alljobs": FIXTURE})
        jobs = self.p.fetch(Target(company="Acme", careers_url=URL), ctx)
        self.assertEqual(len(jobs), 1)
        j = jobs[0]
        self.assertEqual(j.title, "Product Manager")
        self.assertEqual(j.url, "https://acme.darwinbox.in/ms/candidatev2/abc123/careers/jobDetails/a1b2c3")
        self.assertEqual(j.location, "Mumbai, India; Pune, India")
        self.assertEqual((j.salary_min, j.currency), (1500000.0, "INR"))
        self.assertIn("roadmap", j.description)
        self.assertEqual(j.source, "darwinbox")


if __name__ == "__main__":
    unittest.main()
