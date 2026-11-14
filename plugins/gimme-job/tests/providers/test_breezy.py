import unittest

from tests.providers._helpers import ctx_with
from scripts.providers import _registry
from scripts.providers._base import Target

RESP = [{"id": "a1b2", "name": "Customer Success Manager", "url": "https://acme.breezy.hr/p/a1b2-customer-success-manager",
         "published_date": "2026-11-04T10:00:00.000Z", "department": "Success", "type": {"id": "fullTime", "name": "Full-Time"},
         "location": {"name": "Berlin", "city": "Berlin", "country": {"name": "Germany", "id": "DE"}, "is_remote": True}}]


class TestBreezy(unittest.TestCase):
    def setUp(self):
        self.p = _registry.get("breezy")

    def test_detect(self):
        self.assertEqual(self.p.detect("https://acme.breezy.hr/").slug, "acme")
        self.assertIsNone(self.p.detect("https://example.com/careers"))

    def test_fetch(self):
        jobs = self.p.fetch(Target(company="Acme", careers_url="https://acme.breezy.hr"), ctx_with({"acme.breezy.hr/json": RESP}))
        self.assertEqual(len(jobs), 1)
        j = jobs[0]
        self.assertEqual((j.title, j.location, j.workplace, j.employment, j.source),
                         ("Customer Success Manager", "Berlin, Germany, Remote", "remote", "fulltime", "breezy"))
        self.assertTrue(j.url.startswith("https://acme.breezy.hr/p/"))


if __name__ == "__main__":
    unittest.main()
