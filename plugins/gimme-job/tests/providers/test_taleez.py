import unittest

from tests.providers._helpers import ctx_with
from scripts.providers import _registry
from scripts.providers._base import Target

FIXTURE = {
    "name": "Acme", "url": "https://acme.taleez.com",
    "jobs": [{
        "id": 4321, "label": "Chargé de recrutement", "slug": "charge-de-recrutement-4321",
        "contract": "PERMANENT", "lang": "fr", "remote": True,
        "creationDate": 1759300000000, "publishDate": 1760000000000,
        "location": {"city": "Lyon", "region": "Auvergne-Rhône-Alpes", "country": "FR"},
    }],
}


class TestTaleez(unittest.TestCase):
    def setUp(self):
        self.p = _registry.get("taleez")

    def test_detect(self):
        self.assertEqual(self.p.detect("https://acme.taleez.com/").slug, "acme")
        self.assertIsNone(self.p.detect("https://www.taleez.com/"))
        self.assertIsNone(self.p.detect("https://example.com/"))

    def test_fetch(self):
        ctx = ctx_with({"acme.taleez.com/api/careez": FIXTURE})
        jobs = self.p.fetch(Target(company="Acme", slug="acme"), ctx)
        self.assertEqual(len(jobs), 1)
        j = jobs[0]
        self.assertEqual(j.title, "Chargé de recrutement")
        self.assertEqual(j.url, "https://taleez.com/apply/charge-de-recrutement-4321")
        self.assertEqual(j.location, "Lyon, Auvergne-Rhône-Alpes, France, Remote")
        self.assertEqual(j.source, "taleez")
        self.assertTrue(j.posted_at.startswith("2025-"))


if __name__ == "__main__":
    unittest.main()
