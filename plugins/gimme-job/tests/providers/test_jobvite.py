import unittest

from tests.providers._helpers import ctx_with
from scripts.providers import _registry
from scripts.providers._base import Target

BOARD = "<script>var cfg = { companyEId: 'qA1bC2dE3f' };</script>"
XML = """<?xml version="1.0"?><result><job><id>oAb1</id><title>Account Executive</title>
<detail-url>http://jobs.jobvite.com/acme/job/oAb1</detail-url><location>Boston, MA</location><date>11/03/2026</date></job>
<job><id>oAb1</id><title>Account Executive</title><detail-url>http://jobs.jobvite.com/acme/job/oAb1</detail-url><location>Remote</location></job></result>"""


class TestJobvite(unittest.TestCase):
    def setUp(self):
        self.p = _registry.get("jobvite")

    def test_detect(self):
        self.assertEqual(self.p.detect("https://jobs.jobvite.com/acme/jobs").slug, "acme")
        self.assertIsNone(self.p.detect("https://example.com/careers"))

    def test_fetch(self):
        ctx = ctx_with({"CompanyJobs/Xml.aspx?c=qA1bC2dE3f": XML, "jobs.jobvite.com/acme": BOARD})
        jobs = self.p.fetch(Target(company="Acme", slug="acme"), ctx)
        self.assertEqual(len(jobs), 1)
        j = jobs[0]
        self.assertEqual((j.title, j.location, j.source), ("Account Executive", "Boston, MA · Remote", "jobvite"))
        self.assertEqual(j.url, "https://jobs.jobvite.com/acme/job/oAb1")
        self.assertTrue(j.posted_at.startswith("2026-11-03"))


if __name__ == "__main__":
    unittest.main()
