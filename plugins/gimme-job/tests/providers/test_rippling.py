import unittest

from tests.providers._helpers import ctx_with
from scripts.providers import _registry
from scripts.providers._base import Target

RESP = {"items": [{"id": "r1", "name": "Support Specialist", "url": "https://ats.rippling.com/acme/jobs/r1",
                   "department": {"name": "Support"}, "locations": [{"name": "Remote (US)"}, {"name": "Dublin, Ireland"}]}]}


class TestRippling(unittest.TestCase):
    def setUp(self):
        self.p = _registry.get("rippling")

    def test_detect(self):
        self.assertEqual(self.p.detect("https://ats.rippling.com/acme/jobs").slug, "acme")
        self.assertIsNone(self.p.detect("https://example.com/careers"))

    def test_fetch(self):
        jobs = self.p.fetch(Target(company="Acme", slug="acme"), ctx_with({"/api/v2/board/acme/jobs": RESP}))
        self.assertEqual(len(jobs), 1)
        j = jobs[0]
        self.assertEqual((j.title, j.location, j.department, j.source), ("Support Specialist", "Remote (US) · Dublin, Ireland", "Support", "rippling"))
        self.assertEqual(j.url, "https://ats.rippling.com/acme/jobs/r1")


if __name__ == "__main__":
    unittest.main()
