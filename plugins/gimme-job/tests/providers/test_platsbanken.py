import unittest

from tests.providers._helpers import ctx_with
from scripts.providers import _registry
from scripts.providers._base import Target

FIXTURE = {"hits": [{
    "id": "29876543", "headline": "Backend-utvecklare",
    "employer": {"name": "Acme AB"},
    "workplace_address": {"city": "Stockholm", "municipality": "Stockholm", "region": "Stockholms län", "country": "Sverige"},
    "description": {"text": "Vi söker en utvecklare."},
    "publication_date": "2026-11-10T08:00:00", "application_deadline": "2026-12-01T23:59:59",
}]}


class TestPlatsbanken(unittest.TestCase):
    def test_fetch(self):
        p = _registry.get("platsbanken")
        jobs = p.fetch(Target(query="utvecklare"), ctx_with({"jobtechdev.se/search": FIXTURE}))
        self.assertEqual(len(jobs), 1)
        j = jobs[0]
        self.assertEqual(j.url, "https://arbetsformedlingen.se/platsbanken/annonser/29876543")
        self.assertEqual((j.company, j.location), ("Acme AB", "Stockholm, Stockholms län, Sverige"))
        self.assertIn("utvecklare", j.description)
        self.assertEqual(j.source, "platsbanken")


if __name__ == "__main__":
    unittest.main()
