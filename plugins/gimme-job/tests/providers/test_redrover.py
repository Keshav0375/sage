import unittest

from tests.providers._helpers import ctx_with
from scripts.providers import _registry
from scripts.providers._base import Target

FIXTURE = {"data": {"jobSeekerSiteUnauthenticated": {"jobPostingSearch": {"hasMoreData": False, "results": [
    {"id": 101, "name": "Substitute Teacher", "organizationName": "Acme USD", "location": {"name": "Springfield"},
     "activePublicOnDateUtc": "2026-10-01T00:00:00Z", "closedOnDateUtc": None, "allowsRemote": False},
    {"id": 102, "name": "Internal Only", "organizationName": "Acme USD", "location": {"name": "X"},
     "activePublicOnDateUtc": None, "closedOnDateUtc": None, "allowsRemote": False},
]}}}}


class TestRedRover(unittest.TestCase):
    def setUp(self):
        self.p = _registry.get("redrover")

    def test_detect(self):
        t = self.p.detect("https://jobs.redroverk12.com/org/4242/jobs")
        self.assertEqual(t.slug, "4242")
        self.assertIsNone(self.p.detect("https://jobs.redroverk12.com/"))
        self.assertIsNone(self.p.detect("https://example.com/org/4242"))

    def test_fetch(self):
        ctx = ctx_with({"api.redroverk12.com/graphql": FIXTURE})
        jobs = self.p.fetch(Target(company="Acme USD", slug="4242"), ctx)
        self.assertEqual(len(jobs), 1)
        j = jobs[0]
        self.assertEqual(j.url, "https://jobs.redroverk12.com/org/4242/opening/101")
        self.assertEqual(j.location, "Springfield - Acme USD")
        self.assertTrue(j.posted_at.startswith("2026-10-01"))
        self.assertEqual(j.source, "redrover")


if __name__ == "__main__":
    unittest.main()
