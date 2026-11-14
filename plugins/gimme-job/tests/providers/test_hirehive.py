import unittest

from tests.providers._helpers import ctx_with
from scripts.providers import _registry
from scripts.providers._base import Target

FIXTURE = {
    "meta": {"has_next_page": False},
    "links": {},
    "items": [{
        "id": 77, "title": "Product Designer",
        "hosted_url": "https://acme.hirehive.com/product-designer-ab12",
        "location": "Leeds", "country": {"name": "United Kingdom"}, "language": {"code": "en"},
        "published_date": "2026-10-10T08:00:00Z",
        "description": {"html": "<p>Design <b>things</b></p>", "text": "Design things"},
        "compensation_tiers": [{"type": "range_salary", "interval": "year", "min_value": 40000,
                                "max_value": 50000, "currency_code": "gbp"}],
    }],
}


class TestHireHive(unittest.TestCase):
    def setUp(self):
        self.p = _registry.get("hirehive")

    def test_detect(self):
        self.assertEqual(self.p.detect("https://acme.hirehive.com/").slug, "acme")
        self.assertIsNone(self.p.detect("https://www.hirehive.com/"))
        self.assertIsNone(self.p.detect("https://example.com/"))

    def test_fetch(self):
        ctx = ctx_with({"acme.hirehive.com/api/v2/jobs": FIXTURE})
        jobs = self.p.fetch(Target(company="Acme", slug="acme"), ctx)
        self.assertEqual(len(jobs), 1)
        j = jobs[0]
        self.assertEqual(j.title, "Product Designer")
        self.assertEqual(j.url, "https://acme.hirehive.com/product-designer-ab12")
        self.assertEqual(j.location, "Leeds, United Kingdom")
        self.assertEqual((j.salary_min, j.salary_max, j.currency), (40000.0, 50000.0, "GBP"))
        self.assertIn("things", j.description)
        self.assertEqual(j.source, "hirehive")


if __name__ == "__main__":
    unittest.main()
