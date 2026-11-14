import unittest

from tests.providers._helpers import ctx_with
from scripts.providers._base import Target
from scripts.providers.germantechjobs import PROVIDER

RSS = '''<?xml version="1.0"?><rss version="2.0"><channel><title>GTJ</title>
<item><title>Senior Backend Engineer @ Acme GmbH [70.000 - 90.000 €]</title><link>https://germantechjobs.de/jobs/Senior-Backend-Engineer/Java/12345?utm=x</link>
<description><![CDATA[<p>Work on <b>Java</b></p>]]></description><pubDate>Fri, 10 Oct 2025 08:00:00 +0000</pubDate></item>
<item><title>No company here</title><link>https://germantechjobs.de/jobs/x/1</link></item>
</channel></rss>'''


class TestGermanTechJobs(unittest.TestCase):
    def test_fetch(self):
        jobs = PROVIDER.fetch(Target(), ctx_with({"germantechjobs.de/rss": RSS}))
        self.assertEqual(len(jobs), 1)
        j = jobs[0]
        self.assertEqual((j.title, j.company), ("Senior Backend Engineer", "Acme GmbH"))
        self.assertEqual(j.url, "https://germantechjobs.de/jobs/Senior-Backend-Engineer/Java/12345")
        self.assertIn("Java", j.description)
        self.assertTrue(j.posted_at.startswith("2025-10-10"))


if __name__ == "__main__":
    unittest.main()
