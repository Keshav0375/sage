import json
import unittest

from tests.providers._helpers import ctx_with
from scripts.providers import _registry
from scripts.providers._base import Target

PAGE = '<html><script id="__NEXT_DATA__" type="application/json">%s</script></html>' % json.dumps(
    {"props": {"pageProps": {"pageData": {"company": {"id": 4242, "domain": "acme.com"}}}}})

GQL = {"data": {"publicJobs": {
    "items": [{
        "id": 9001, "title": "Data Analyst", "createdAt": "2026-10-02T10:00:00Z",
        "descriptionHtml": "<p>Analyse <b>data</b></p>", "language": {"iso6391": "en"},
        "workplaceType": "HYBRID", "remoteType": None, "remoteRegion": None,
        "city": {"cityName": "Vienna", "countryName": "Austria"}, "country": {"name": "Austria"},
    }],
    "pageInfo": {"pageCount": 1},
}}}


class TestJoin(unittest.TestCase):
    def setUp(self):
        self.p = _registry.get("join")

    def test_detect(self):
        self.assertEqual(self.p.detect("https://join.com/companies/acme").slug, "acme")
        self.assertIsNone(self.p.detect("https://example.com/companies/acme"))

    def test_fetch(self):
        ctx = ctx_with({"join.com/companies/acme": PAGE, "candidate-api/graphql": GQL})
        jobs = self.p.fetch(Target(company="Acme", slug="acme"), ctx)
        self.assertEqual(len(jobs), 1)
        j = jobs[0]
        self.assertEqual(j.title, "Data Analyst")
        self.assertEqual(j.url, "https://join.com/companies/acme/9001")
        self.assertEqual(j.location, "Vienna, Austria (hybrid)")
        self.assertEqual(j.workplace, "hybrid")
        self.assertIn("data", j.description)
        self.assertEqual(j.source, "join")


if __name__ == "__main__":
    unittest.main()
