import json
import unittest

from tests.providers._helpers import ctx_with
from scripts.providers import _registry
from scripts.providers._base import Target

HTML = """<html><body><ul>
<li><div><h3>Strategy &amp; Operations Manager</h3><p class="l103df">Google | Mountain View, CA, USA; New York, NY, USA; +2 more</p>
<a class="WpHJef" href="jobs/results/112233445566-strategy-operations-manager?q=x" aria-label="Learn more about Strategy &amp; Operations Manager">Learn more</a></div></li>
</ul></body></html>"""


class TestGoogle(unittest.TestCase):
    def test_fetch(self):
        ctx = ctx_with({"google.com/about/careers/applications/jobs/results": HTML})
        jobs = _registry.get("google").fetch(Target(query="strategy"), ctx)
        self.assertEqual(len(jobs), 1)
        j = jobs[0]
        self.assertEqual((j.title, j.company), ("Strategy & Operations Manager", "Google"))
        self.assertEqual(j.location, "Mountain View, CA, USA; New York, NY, USA")
        self.assertEqual(j.url, "https://www.google.com/about/careers/applications/jobs/results/112233445566-strategy-operations-manager")
        self.assertEqual(j.source_id, "112233445566")


if __name__ == "__main__":
    unittest.main()
