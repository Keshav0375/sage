import json
import unittest

from tests.providers._helpers import ctx_with
from scripts.providers import _registry
from scripts.providers._base import Target

RSS = """<?xml version="1.0"?><rss version="2.0"><channel><title>x</title>
<item><title>Backend Engineer at Acme</title><link>https://startup.jobs/backend-engineer-acme-123?utm=1</link>
<pubDate>Mon, 02 Nov 2026 10:00:00 +0000</pubDate>
<description><![CDATA[Great team.
Remote · $100k - $140k]]></description></item>
<item><title>No employer here</title><link>https://startup.jobs/x-1</link></item>
</channel></rss>"""


class TestStartupJobs(unittest.TestCase):
    def test_fetch(self):
        jobs = _registry.get("startup-jobs").fetch(Target(), ctx_with({"startup.jobs/feeds/jobs": RSS}))
        self.assertEqual(len(jobs), 1)
        j = jobs[0]
        self.assertEqual((j.title, j.company, j.location), ("Backend Engineer", "Acme", "Remote"))
        self.assertEqual(j.url, "https://startup.jobs/backend-engineer-acme-123")
        self.assertTrue(j.posted_at.startswith("2026-11-02"))


if __name__ == "__main__":
    unittest.main()
