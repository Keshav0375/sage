import json
import unittest

from tests.providers._helpers import ctx_with
from scripts.providers import _registry
from scripts.providers._base import Target

RSS = """<?xml version="1.0"?><rss version="2.0" xmlns:job_listing="https://x/job_listing" xmlns:content="http://purl.org/rss/1.0/modules/content/"><channel>
<item><title>Editor</title><link>https://jobs.example.org/job/editor/</link>
<pubDate>Mon, 02 Nov 2026 10:00:00 +0000</pubDate>
<job_listing:location>Remote</job_listing:location><job_listing:company>Example Media</job_listing:company>
<content:encoded><![CDATA[<p>Edit things.</p>]]></content:encoded></item>
<item><title>Foreign</title><link>https://other.example/job/x/</link></item></channel></rss>"""


class TestWpJobManager(unittest.TestCase):
    def test_fetch(self):
        p = _registry.get("wp-job-manager")
        ctx = ctx_with({"jobs.example.org/?feed=job_feed": RSS})
        jobs = p.fetch(Target(careers_url="https://jobs.example.org/jobs/"), ctx)
        self.assertEqual(len(jobs), 1)
        j = jobs[0]
        self.assertEqual((j.title, j.company, j.location), ("Editor", "Example Media", "Remote"))
        self.assertEqual(j.url, "https://jobs.example.org/job/editor/")

    def test_non_rss_fails(self):
        from scripts.providers._base import ProviderError
        with self.assertRaises(ProviderError):
            _registry.get("wp-job-manager").fetch(Target(careers_url="https://jobs.example.org/"),
                                                 ctx_with({"jobs.example.org": "<html>nope</html>"}))


if __name__ == "__main__":
    unittest.main()
