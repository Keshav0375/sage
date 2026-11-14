import json
import unittest

from tests.providers._helpers import ctx_with
from scripts.providers import _registry
from scripts.providers._base import Target

LD = {"@type": "ItemList", "itemListElement": [{"item": {
    "@type": "JobPosting", "title": "Analista de Datos",
    "url": "http://acme.hiringroom.com/jobs/get_vacancy/abc123def",
    "description": "<p>Analiza <b>datos</b></p>", "datePosted": "2026-10-10",
    "jobLocation": {"address": {"addressLocality": "Buenos Aires", "addressCountry": "AR"}},
}}]}
JSON_LD_PAGE = '<html><script type="application/ld+json">%s</script></html>' % json.dumps(LD)
LEGACY_PAGE = """<html><a href="/jobs/get_vacancy/0123abcd"><div><h4 class="x name__vacancy">Vendedor</h4>
<i class="hr-Location-pin"></i> Lima</div></a></html>"""


class TestHiringRoom(unittest.TestCase):
    def setUp(self):
        self.p = _registry.get("hiringroom")

    def test_detect(self):
        self.assertEqual(self.p.detect("https://acme.hiringroom.com/jobs").slug, "acme")
        self.assertIsNone(self.p.detect("https://example.com/jobs"))

    def test_fetch_jsonld(self):
        ctx = ctx_with({"acme.hiringroom.com/jobs": JSON_LD_PAGE})
        jobs = self.p.fetch(Target(company="Acme", careers_url="https://acme.hiringroom.com/jobs"), ctx)
        self.assertEqual(len(jobs), 1)
        j = jobs[0]
        self.assertEqual(j.title, "Analista de Datos")
        self.assertEqual(j.url, "https://acme.hiringroom.com/jobs/get_vacancy/abc123def")
        self.assertEqual(j.location, "Buenos Aires, AR")
        self.assertIn("datos", j.description)
        self.assertEqual(j.source, "hiringroom")

    def test_fetch_legacy(self):
        ctx = ctx_with({"acme.hiringroom.com/jobs": LEGACY_PAGE})
        jobs = self.p.fetch(Target(company="Acme", careers_url="https://acme.hiringroom.com/jobs"), ctx)
        self.assertEqual((jobs[0].title, jobs[0].location), ("Vendedor", "Lima"))


if __name__ == "__main__":
    unittest.main()
