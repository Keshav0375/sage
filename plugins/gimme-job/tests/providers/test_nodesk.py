import json
import unittest

from tests.providers._helpers import ctx_with
from scripts.providers import _registry
from scripts.providers._base import Target

RSS = """<?xml version="1.0"?><rss version="2.0"><channel>
<item><title>Customer Success Manager at Buffer</title><link>https://nodesk.co/remote-jobs/buffer-csm/</link>
<pubDate>Tue, 03 Nov 2026 12:00:00 +0000</pubDate></item>
<item><title>Offsite</title><link>https://evil.example/x</link></item></channel></rss>"""


class TestNodesk(unittest.TestCase):
    def test_fetch(self):
        jobs = _registry.get("nodesk").fetch(Target(), ctx_with({"nodesk.co/remote-jobs/index.xml": RSS}))
        self.assertEqual(len(jobs), 1)
        self.assertEqual((jobs[0].title, jobs[0].company), ("Customer Success Manager", "Buffer"))
        self.assertEqual(jobs[0].url, "https://nodesk.co/remote-jobs/buffer-csm/")


if __name__ == "__main__":
    unittest.main()
