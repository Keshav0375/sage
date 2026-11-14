import unittest

from tests.providers._helpers import ctx_with
from scripts.providers import _registry
from scripts.providers._base import Target

FIXTURE = [{
    "id": "p1", "title": "Teaching Assistant", "hostedUrl": "https://secure.collage.co/jobs/acme/p1",
    "location": ["Boston, MA", "Remote"], "department": "Education", "commitment": "Part-time",
    "descriptionPlain": "Help students learn.", "createdDate": "2026-10-07T00:00:00Z",
}]


class TestCollage(unittest.TestCase):
    def setUp(self):
        self.p = _registry.get("collage")

    def test_detect(self):
        t = self.p.detect("https://secure.collage.co/jobs/acme")
        self.assertEqual(t.slug, "acme")
        self.assertEqual(t.api_url, "https://api.collage.co/v1/positions/acme")
        self.assertIsNone(self.p.detect("https://example.com/jobs/acme"))

    def test_fetch(self):
        ctx = ctx_with({"api.collage.co/v1/positions/acme": FIXTURE})
        jobs = self.p.fetch(Target(company="Acme", slug="acme"), ctx)
        self.assertEqual(len(jobs), 1)
        j = jobs[0]
        self.assertEqual(j.title, "Teaching Assistant")
        self.assertEqual(j.url, "https://secure.collage.co/jobs/acme/p1")
        self.assertEqual(j.location, "Boston, MA; Remote")
        self.assertIn("Part-time", j.description)
        self.assertEqual(j.source, "collage")


if __name__ == "__main__":
    unittest.main()
