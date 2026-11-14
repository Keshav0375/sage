import unittest

from tests.providers._helpers import ctx_with
from scripts.providers import _registry
from scripts.providers._base import Target

GUID = "0a1b2c3d-1111-2222-3333-444455556666"
SHELL = '<html><script src="/ats/documents/%s/careerportal/app.js"></script></html>' % GUID
ROWS = [{
    "id": 12, "title": "  QA   Engineer ", "publishedOn": "2026-10-03T00:00:00Z",
    "description": "<p>Test <b>software</b></p>",
    "jobLocations": [{"name": "HQ - Tower 2", "city": "Hyderabad", "countryName": "India"}],
}]


class TestKeka(unittest.TestCase):
    def setUp(self):
        self.p = _registry.get("keka")

    def test_detect(self):
        self.assertEqual(self.p.detect("https://acme.keka.com/careers").slug, "acme")
        self.assertIsNone(self.p.detect("https://www.keka.com/"))
        self.assertIsNone(self.p.detect("https://example.com/"))

    def test_fetch(self):
        ctx = ctx_with({"/careers/api/embedjobs/default/active/" + GUID: ROWS,
                        "acme.keka.com/careers": SHELL})
        jobs = self.p.fetch(Target(company="Acme", careers_url="https://acme.keka.com/careers"), ctx)
        self.assertEqual(len(jobs), 1)
        j = jobs[0]
        self.assertEqual(j.title, "QA Engineer")
        self.assertEqual(j.url, "https://acme.keka.com/careers/jobdetails/12")
        self.assertEqual(j.location, "Hyderabad, India")
        self.assertIn("software", j.description)
        self.assertEqual(j.source, "keka")


if __name__ == "__main__":
    unittest.main()
