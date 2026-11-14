import unittest

from tests.providers._helpers import ctx_with
from scripts.providers._base import Target
from scripts.providers.arbeitnow import PROVIDER

FIXTURE = {"data": [{
    "slug": "python-dev-acme-berlin-123", "company_name": "Acme GmbH", "title": "Python Developer",
    "description": "<p>Build <b>APIs</b></p>", "remote": True, "url": "https://www.arbeitnow.com/jobs/companies/acme/python-dev-123",
    "tags": ["Software Development"], "job_types": ["full time"], "location": "Berlin", "created_at": 1760000000}]}


class TestArbeitnow(unittest.TestCase):
    def test_fetch(self):
        ctx = ctx_with({"arbeitnow.com/api/job-board-api": FIXTURE})
        jobs = PROVIDER.fetch(Target(), ctx)
        self.assertEqual(len(jobs), 1)
        j = jobs[0]
        self.assertEqual((j.title, j.company, j.source, j.workplace), ("Python Developer", "Acme GmbH", "arbeitnow", "remote"))
        self.assertEqual(j.location, "Berlin")
        self.assertIn("APIs", j.description)
        self.assertTrue(j.posted_at.startswith("2025-10"))
        self.assertTrue(j.url.startswith("https://"))


if __name__ == "__main__":
    unittest.main()
