import json
import unittest

from tests.providers._helpers import ctx_with
from scripts.providers import _registry
from scripts.providers._base import Target

INDEX = '<?xml version="1.0"?><sitemapindex><sitemap><loc>https://careers.acme.com/sitemap-jobs.xml</loc></sitemap><sitemap><loc>https://careers.acme.com/sitemap-blog.xml</loc></sitemap></sitemapindex>'
JOBS = '<?xml version="1.0"?><urlset><url><loc>https://careers.acme.com/jobs/1234/senior-qa-engineer</loc></url><url><loc>https://careers.acme.com/about</loc></url><url><loc>https://other.com/jobs/9/x</loc></url></urlset>'
DETAIL = '<html><script type="application/ld+json">{"@type":"JobPosting","title":"Senior QA Engineer","datePosted":"2026-10-01","description":"<p>Test things</p>","jobLocation":{"address":{"addressLocality":"Toronto","addressCountry":"CA"}}}</script></html>'
OPTS = {"job_path": r"^/jobs/(?<posting_id>\d+)/(?<slug>[a-z0-9-]+)$", "index_filter": "sitemap-jobs"}


class TestSitemap(unittest.TestCase):
    def test_index_and_filter(self):
        ctx = ctx_with({"sitemap-jobs.xml": JOBS, "sitemap.xml": INDEX})
        jobs = _registry.get("sitemap").fetch(
            Target(company="Acme", careers_url="https://careers.acme.com/sitemap.xml", options=OPTS), ctx)
        self.assertEqual(len(jobs), 1)
        j = jobs[0]
        self.assertEqual((j.title, j.company, j.source_id), ("Senior QA Engineer", "Acme", "1234"))
        self.assertEqual(j.url, "https://careers.acme.com/jobs/1234/senior-qa-engineer")
        self.assertFalse(any("blog" in c[1] for c in ctx.http.transport.calls))

    def test_details(self):
        ctx = ctx_with({"/jobs/1234/": DETAIL, "sitemap.xml": JOBS})
        jobs = _registry.get("sitemap").fetch(
            Target(company="Acme", careers_url="https://careers.acme.com/sitemap.xml",
                   options={**OPTS, "fetchDetails": True}), ctx)
        self.assertEqual(jobs[0].location, "Toronto, CA")
        self.assertIn("Test things", jobs[0].description)
        self.assertTrue(jobs[0].posted_at.startswith("2026-10-01"))

    def test_needs_job_path(self):
        from scripts.providers._base import ProviderError
        with self.assertRaises(ProviderError):
            _registry.get("sitemap").fetch(Target(careers_url="https://careers.acme.com/sitemap.xml"), ctx_with({}))


if __name__ == "__main__":
    unittest.main()
