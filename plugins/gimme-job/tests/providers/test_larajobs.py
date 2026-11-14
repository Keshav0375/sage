import unittest

from tests.providers._helpers import ctx_with
from scripts.providers._base import Target
from scripts.providers.larajobs import PROVIDER

RSS = '''<?xml version="1.0"?><rss version="2.0" xmlns:job="https://larajobs.com/ns" xmlns:dc="http://purl.org/dc/elements/1.1/"><channel>
<item><title>Senior Laravel Developer</title><link>https://larajobs.com/job/1234</link><job:company>Acme</job:company>
<job:location>Remote (Worldwide)</job:location><pubDate>Mon, 20 Oct 2025 12:00:00 +0000</pubDate></item></channel></rss>'''


class TestLaraJobs(unittest.TestCase):
    def test_fetch(self):
        jobs = PROVIDER.fetch(Target(), ctx_with({"larajobs.com/feed": RSS}))
        self.assertEqual(len(jobs), 1)
        j = jobs[0]
        self.assertEqual((j.title, j.company, j.location, j.url), ("Senior Laravel Developer", "Acme", "Remote (Worldwide)", "https://larajobs.com/job/1234"))
        self.assertTrue(j.posted_at.startswith("2025-10-20"))


if __name__ == "__main__":
    unittest.main()
