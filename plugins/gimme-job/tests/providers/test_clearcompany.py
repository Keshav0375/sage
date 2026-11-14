import unittest

from tests.providers._helpers import ctx_with
from scripts.providers import _registry
from scripts.providers._base import Target

SITE = "11111111-2222-3333-4444-555555555555"
FIXTURE = {"totalCount": 1, "results": [{
    "id": "r1", "positionTitle": "Warehouse Associate", "userDefinedId": "REQ-9",
    "applyLink": "https://acme.clearcompany.com/careers/jobs/abc/apply",
    "postedDate": "2026-10-05T12:00:00Z", "description": "<p>Lift <b>boxes</b></p>",
    "locations": [{"city": "Denver", "subdivisionFullName": "Colorado", "country": "United States", "isRemote": False}],
}]}


class TestClearCompany(unittest.TestCase):
    def setUp(self):
        self.p = _registry.get("clearcompany")

    def test_detect(self):
        t = self.p.detect(f"https://careers-api.clearcompany.com/v1/{SITE}")
        self.assertEqual(t.slug, SITE)
        self.assertEqual(self.p.detect(f"https://careers-content.clearcompany.com/x.js?siteId={SITE}").slug, SITE)
        self.assertIsNone(self.p.detect("https://example.com/"))

    def test_fetch(self):
        ctx = ctx_with({f"careers-api.clearcompany.com/v1/{SITE}": FIXTURE})
        jobs = self.p.fetch(Target(company="Acme", slug=SITE), ctx)
        self.assertEqual(len(jobs), 1)
        j = jobs[0]
        self.assertEqual(j.title, "Warehouse Associate")
        self.assertEqual(j.url, "https://acme.clearcompany.com/careers/jobs/abc/apply")
        self.assertEqual(j.location, "Denver, Colorado, United States")
        self.assertEqual(j.source_id, "REQ-9")
        self.assertIn("boxes", j.description)
        self.assertEqual(j.source, "clearcompany")


if __name__ == "__main__":
    unittest.main()
