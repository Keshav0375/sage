import unittest

from tests.providers._helpers import ctx_with
from scripts.providers import _registry
from scripts.providers._base import Target

FIXTURE = """<?xml version="1.0"?>
<rss xmlns:tt="https://teamtailor.com/locations" version="2.0"><channel>
<item><title>Data Engineer</title><link>https://acme.teamtailor.com/jobs/1-data-engineer</link>
<guid>1</guid><pubDate>Mon, 03 Nov 2025 10:00:00 +0000</pubDate>
<department>Data</department><remoteStatus>none</remoteStatus>
<description><![CDATA[<p>Pipelines.</p>]]></description>
<tt:locations><tt:location><tt:city>Stockholm</tt:city><tt:country>Sweden</tt:country></tt:location></tt:locations></item>
<item><title>Remote Dev</title><link>https://acme.teamtailor.com/jobs/2-dev</link><remoteStatus>fully</remoteStatus></item>
<item><title></title><link>https://acme.teamtailor.com/jobs/3</link></item>
</channel></rss>"""


class TestTeamtailor(unittest.TestCase):
    def setUp(self):
        self.p = _registry.get("teamtailor")

    def test_detect(self):
        t = self.p.detect("https://acme.teamtailor.com/jobs")
        self.assertEqual((t.slug, t.api_url), ("acme", "https://acme.teamtailor.com/jobs.rss"))
        self.assertIsNone(self.p.detect("https://example.com/careers"))

    def test_fetch(self):
        ctx = ctx_with({"acme.teamtailor.com/jobs.rss": FIXTURE})
        jobs = self.p.fetch(self.p.detect("https://acme.teamtailor.com/jobs"), ctx)
        self.assertEqual(len(jobs), 2)
        self.assertEqual((jobs[0].title, jobs[0].location, jobs[0].department, jobs[0].source), ("Data Engineer", "Stockholm, Sweden", "Data", "teamtailor"))
        self.assertIn("Pipelines", jobs[0].description)
        self.assertTrue(jobs[0].posted_at.startswith("2025-11-03"))
        self.assertEqual((jobs[1].location, jobs[1].workplace), ("Remote", "remote"))


if __name__ == "__main__":
    unittest.main()

