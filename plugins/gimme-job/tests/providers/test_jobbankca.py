import unittest

from tests.providers._helpers import ctx_with
from scripts.providers import _registry
from scripts.providers._base import Target

FIXTURE = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
<entry><title>Software Developer</title>
<link rel="alternate" href="https://www.jobbank.gc.ca/jobsearch/jobposting/12345"/>
<id>tag:jobbank:12345</id><updated>2026-11-05T10:00:00Z</updated>
<summary type="html">&lt;strong&gt;Employer:&lt;/strong&gt; Maple Corp &lt;br/&gt;&lt;strong&gt;Location:&lt;/strong&gt; Ottawa (ON) &lt;br/&gt;</summary></entry>
<entry><title>Offsite</title><link rel="alternate" href="https://evil.example/x"/></entry>
</feed>"""


class TestJobBankCA(unittest.TestCase):
    def setUp(self):
        self.p = _registry.get("jobbankca")

    def test_detect_none(self):
        self.assertIsNone(self.p.detect("https://www.jobbank.gc.ca/"))

    def test_fetch(self):
        ctx = ctx_with({"jobSearchRSSfeed?searchstring=developer": FIXTURE})
        jobs = self.p.fetch(Target(query="developer"), ctx)
        self.assertEqual(len(jobs), 1)
        j = jobs[0]
        self.assertEqual((j.title, j.company, j.location, j.country, j.source), ("Software Developer", "Maple Corp", "Ottawa (ON)", "CA", "jobbankca"))
        self.assertEqual(j.url, "https://www.jobbank.gc.ca/jobsearch/jobposting/12345")
        self.assertTrue(j.posted_at.startswith("2026-11-05"))


if __name__ == "__main__":
    unittest.main()

