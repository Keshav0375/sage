import json
import unittest

from tests.providers._helpers import ctx_with
from scripts.providers import _registry
from scripts.providers._base import Target

RSS = """<?xml version="1.0"?><rss version="2.0" xmlns:job_listing="https://jobspresso.co/job_listing" xmlns:content="http://purl.org/rss/1.0/modules/content/"><channel>
<item><title>Support Lead</title><link>https://jobspresso.co/job/support-lead/</link>
<pubDate>Mon, 02 Nov 2026 10:00:00 +0000</pubDate>
<job_listing:location>Worldwide</job_listing:location><job_listing:company>Acme</job_listing:company>
<content:encoded><![CDATA[<p>Lead the <b>support</b> team.</p>]]></content:encoded></item></channel></rss>"""


class TestJobspresso(unittest.TestCase):
    def test_fetch(self):
        jobs = _registry.get("jobspresso").fetch(Target(), ctx_with({"jobspresso.co/feed/job_feed": RSS}))
        self.assertEqual(len(jobs), 1)
        j = jobs[0]
        self.assertEqual((j.title, j.company, j.location), ("Support Lead", "Acme", "Worldwide"))
        self.assertIn("support team", j.description)


if __name__ == "__main__":
    unittest.main()
