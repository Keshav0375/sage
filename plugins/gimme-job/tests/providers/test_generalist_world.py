import json
import unittest

from tests.providers._helpers import ctx_with
from scripts.providers import _registry
from scripts.providers._base import Target

HTML = """<html><body><div class="gw-jobs-section" data-jobs-container>
<a class="gw-job-card" href="/jobs/ops-lead-acme/" data-region="eu">
<div class="gw-job-title">Operations Lead</div><div class="gw-job-company">Acme</div>
<span class="gw-location">Berlin</span><p class="gw-job-description">Run ops &amp; growth.</p></a>
<a class="gw-job-card" href="/jobs/chief-of-staff/" data-region="remote">
<div class="gw-job-title">Chief of Staff</div><div class="gw-job-company">Beta</div></a>
</div></body></html>"""


class TestGeneralistWorld(unittest.TestCase):
    def test_fetch(self):
        jobs = _registry.get("generalist-world").fetch(Target(), ctx_with({"generalist.world/jobs/": HTML}))
        self.assertEqual(len(jobs), 2)
        self.assertEqual((jobs[0].title, jobs[0].company, jobs[0].location), ("Operations Lead", "Acme", "Berlin"))
        self.assertEqual(jobs[0].url, "https://generalist.world/jobs/ops-lead-acme/")
        self.assertIn("ops & growth", jobs[0].description)
        self.assertEqual(jobs[1].location, "Remote")


if __name__ == "__main__":
    unittest.main()
