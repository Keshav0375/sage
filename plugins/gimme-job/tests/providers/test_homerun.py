import unittest

from tests.providers._helpers import ctx_with
from scripts.providers import _registry
from scripts.providers._base import Target

FEED = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>Acme jobs</title>
  <entry>
    <author><name>Acme</name></author>
    <title type="text">Backend Engineer</title>
    <link rel="alternate" type="text/html" href="https://acme.homerun.co/backend-engineer"></link>
    <id>job_abc</id>
    <description type="html"><![CDATA[<p>Build <b>APIs</b></p>]]></description>
    <location><name>Amsterdam</name></location>
    <salary_indication>&#8364;60000.00 to &#8364;70000.00 per year</salary_indication>
    <updated>2026-09-29 15:07:45</updated>
  </entry>
</feed>"""


class TestHomerun(unittest.TestCase):
    def setUp(self):
        self.p = _registry.get("homerun")

    def test_detect(self):
        self.assertEqual(self.p.detect("https://acme.homerun.co/").slug, "acme")
        self.assertEqual(self.p.detect("https://feed.homerun.co/acme").slug, "acme")
        self.assertIsNone(self.p.detect("https://www.homerun.co/"))
        self.assertIsNone(self.p.detect("https://example.com/"))

    def test_fetch(self):
        ctx = ctx_with({"feed.homerun.co/acme": FEED})
        jobs = self.p.fetch(Target(company="Acme", slug="acme"), ctx)
        self.assertEqual(len(jobs), 1)
        j = jobs[0]
        self.assertEqual(j.title, "Backend Engineer")
        self.assertEqual(j.url, "https://acme.homerun.co/backend-engineer")
        self.assertEqual(j.location, "Amsterdam")
        self.assertIn("APIs", j.description)
        self.assertEqual((j.salary_min, j.salary_max), (60000.0, 70000.0))
        self.assertTrue(j.posted_at.startswith("2026-09-29"))
        self.assertEqual(j.source, "homerun")


if __name__ == "__main__":
    unittest.main()
