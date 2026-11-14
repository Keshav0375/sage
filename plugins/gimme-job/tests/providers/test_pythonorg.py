import json
import unittest

from tests.providers._helpers import ctx_with
from scripts.providers import _registry
from scripts.providers._base import Target

RSS = """<?xml version="1.0"?><rss version="2.0"><channel>
<item><title>Python Developer, Acme Corp</title><link>https://www.python.org/jobs/7777/</link>
<description><![CDATA[Berlin, Germany
<p>Write Python.</p>]]></description><pubDate>Mon, 02 Nov 2026 10:00:00 +0000</pubDate></item>
<item><title>Untitled no comma</title><link>https://www.python.org/jobs/1/</link></item></channel></rss>"""


class TestPythonOrg(unittest.TestCase):
    def test_detect(self):
        p = _registry.get("pythonorg")
        self.assertIsNotNone(p.detect("https://www.python.org/jobs/"))
        self.assertIsNone(p.detect("https://www.python.org/about/"))
        self.assertIsNone(p.detect("https://example.com/jobs/"))

    def test_fetch(self):
        jobs = _registry.get("pythonorg").fetch(Target(), ctx_with({"python.org/jobs/feed/rss": RSS}))
        self.assertEqual(len(jobs), 1)
        j = jobs[0]
        self.assertEqual((j.title, j.company, j.location), ("Python Developer", "Acme Corp", "Berlin, Germany"))
        self.assertIn("Write Python", j.description)


if __name__ == "__main__":
    unittest.main()
