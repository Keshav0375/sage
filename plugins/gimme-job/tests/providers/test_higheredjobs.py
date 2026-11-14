import unittest

from tests.providers._helpers import ctx_with
from scripts.providers import _registry
from scripts.providers._base import Target

RSS = """<?xml version="1.0"?><rss version="2.0"><channel><title>HEJ</title>
<item><title><![CDATA[Director of AI Strategy]]></title>
<link>https://www.higheredjobs.com/details.cfm?JobCode=17899012</link>
<description>Acme University (Boston, MA)</description><pubDate>Mon, 09 Nov 2026 00:00:00 GMT</pubDate></item>
<item><title>Offsite</title><link>https://evil.example/x</link><description>X (Y)</description></item>
</channel></rss>"""


class TestHigherEdJobs(unittest.TestCase):
    def test_fetch(self):
        p = _registry.get("higheredjobs")
        jobs = p.fetch(Target(), ctx_with({"higheredjobs.com/rss/categoryFeed.cfm": RSS}))
        self.assertEqual(len(jobs), 1)
        j = jobs[0]
        self.assertEqual((j.title, j.company, j.location), ("Director of AI Strategy", "Acme University", "Boston, MA"))
        self.assertTrue(j.posted_at.startswith("2026-11-09"))


if __name__ == "__main__":
    unittest.main()
