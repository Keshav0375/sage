import json
import unittest

from tests.providers._helpers import ctx_with
from scripts.providers import _registry
from scripts.providers._base import Target

from scripts.providers import cryptocurrencyjobs as cj

RSS = """<?xml version="1.0"?><rss version="2.0"><channel>
<item><title>Smart Contract Engineer at Uniswap</title><link>https://cryptocurrencyjobs.co/engineering/uniswap-smart-contract-engineer/</link>
<pubDate>Mon, 09 Nov 2026 10:00:00 +0000</pubDate>
<description>This is a full-time position that is 100% remote with no geographical restrictions. Work remotely from anywhere.</description></item>
<item><title>Designer at Foo</title><link>https://cryptocurrencyjobs.co/design/foo/</link>
<description>This is a full-time position that is based in New York NY.</description></item></channel></rss>"""


class TestCryptoJobs(unittest.TestCase):
    def test_fetch(self):
        jobs = _registry.get("cryptocurrencyjobs").fetch(Target(), ctx_with({"cryptocurrencyjobs.co/index.xml": RSS}))
        self.assertEqual(len(jobs), 2)
        self.assertEqual((jobs[0].title, jobs[0].company, jobs[0].location), ("Smart Contract Engineer", "Uniswap", "Remote (worldwide)"))
        self.assertEqual(jobs[1].location, "New York, NY")

    def test_clause(self):
        self.assertEqual(cj.location_from_clause("can be done remotely anywhere in the United States, or Canada"),
                         "Remote (United States, Canada)")


if __name__ == "__main__":
    unittest.main()
