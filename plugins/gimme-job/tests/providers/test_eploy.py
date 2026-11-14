import unittest

from tests.providers._helpers import ctx_with
from scripts.providers import _registry
from scripts.providers._base import Target

SITEMAP = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://jobs.acme.co.uk/vacancies/1234/senior-hr-business-partner.html</loc></url>
  <url><loc>https://jobs.acme.co.uk/vacancies/1234/senior-hr-business-partner.html</loc></url>
  <url><loc>https://jobs.acme.co.uk/about.html</loc></url>
  <url><loc>https://evil.example/vacancies/9/x.html</loc></url>
</urlset>"""


class TestEploy(unittest.TestCase):
    def setUp(self):
        self.p = _registry.get("eploy")

    def test_detect(self):
        self.assertEqual(self.p.detect("https://acme.eploy.net/").slug, "acme")
        self.assertIsNone(self.p.detect("https://example.com/"))

    def test_fetch(self):
        ctx = ctx_with({"jobs.acme.co.uk/live-jobs.xml": SITEMAP})
        jobs = self.p.fetch(Target(company="Acme", careers_url="https://jobs.acme.co.uk/"), ctx)
        self.assertEqual(len(jobs), 1)
        j = jobs[0]
        self.assertEqual(j.title, "Senior HR Business Partner")
        self.assertEqual(j.url, "https://jobs.acme.co.uk/vacancies/1234/senior-hr-business-partner.html")
        self.assertEqual(j.source_id, "1234")
        self.assertEqual(j.source, "eploy")


if __name__ == "__main__":
    unittest.main()
