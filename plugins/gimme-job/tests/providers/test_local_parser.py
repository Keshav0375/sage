import json
import unittest

from tests.providers._helpers import ctx_with
from scripts.providers import _registry
from scripts.providers._base import Target

LD = """<html><script type="application/ld+json">{"@context":"https://schema.org","@type":"JobPosting","title":"Platform Engineer",
"url":"/careers/platform-engineer","datePosted":"2026-10-20","employmentType":"FULL_TIME","jobLocationType":"TELECOMMUTE",
"hiringOrganization":{"@type":"Organization","name":"Acme"},"description":"<p>Build the platform</p>",
"jobLocation":{"@type":"Place","address":{"addressLocality":"Austin","addressRegion":"TX","addressCountry":"US"}}}</script></html>"""
LINKS = """<html><body><a href="/">Home</a><a href="/careers/senior-backend-engineer">Senior Backend Engineer</a>
<a href="/jobs/42-product-designer">Product Designer</a><a href="/about">About us</a><a href="/careers">Careers</a></body></html>"""


class TestLocalParser(unittest.TestCase):
    def test_json_ld(self):
        jobs = _registry.get("local-parser").fetch(Target(careers_url="https://acme.com/careers"), ctx_with({"acme.com/careers": LD}))
        self.assertEqual(len(jobs), 1)
        j = jobs[0]
        self.assertEqual((j.title, j.company, j.location), ("Platform Engineer", "Acme", "Austin, TX, US"))
        self.assertEqual(j.url, "https://acme.com/careers/platform-engineer")
        self.assertEqual((j.employment, j.workplace), ("fulltime", "remote"))

    def test_links_fallback(self):
        jobs = _registry.get("local-parser").fetch(
            Target(company="Acme", careers_url="https://acme.com/careers"), ctx_with({"acme.com/careers": LINKS}))
        self.assertEqual({j.title for j in jobs}, {"Senior Backend Engineer", "Product Designer"})
        self.assertTrue(all(j.company == "Acme" and j.url.startswith("https://acme.com/") for j in jobs))


if __name__ == "__main__":
    unittest.main()
