import unittest

from tests.providers._helpers import ctx_with
from scripts.providers import _registry
from scripts.providers._base import Target

FIXTURE = """<?xml version="1.0"?><rss version="2.0"><channel>
<item><title>Acme: Senior Engineer</title><region>Anywhere in the World</region><category>Programming</category>
<link>https://weworkremotely.com/remote-jobs/acme-senior-engineer</link>
<pubDate>Mon, 03 Nov 2026 10:00:00 +0000</pubDate>
<description><![CDATA[<p>Great <b>job</b>.</p>]]></description></item>
<item><title>Offsite: Bad</title><link>https://evil.example/x</link></item>
<item><title>NoColon Role</title><link>https://weworkremotely.com/remote-jobs/nocolon</link></item>
</channel></rss>"""


class TestWeWorkRemotely(unittest.TestCase):
    def setUp(self):
        self.p = _registry.get("weworkremotely")

    def test_detect_none(self):
        self.assertIsNone(self.p.detect("https://weworkremotely.com/"))

    def test_fetch(self):
        jobs = self.p.fetch(Target(), ctx_with({"weworkremotely.com/remote-jobs.rss": FIXTURE}))
        self.assertEqual(len(jobs), 2)
        j = jobs[0]
        self.assertEqual((j.title, j.company, j.location, j.source), ("Senior Engineer", "Acme", "Anywhere in the World", "weworkremotely"))
        self.assertIn("Great", j.description)
        self.assertTrue(j.posted_at.startswith("2026-11-03"))
        self.assertEqual(jobs[1].company, "")


if __name__ == "__main__":
    unittest.main()

