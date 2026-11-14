import unittest

from tests.providers._helpers import ctx_with
from scripts.providers import _registry
from scripts.providers._base import Target

FIXTURE = {
    "meta": {"total": 1},
    "objects": [{
        "id": 31337, "title": "Support  Specialist",
        "hosted_url": "https://acme.hire.trakstar.com/jobs/fk0abc/",
        "description": "<p>Help <b>users</b></p>",
        "location": {"city": "Austin", "state": "TX", "country": "US"}, "allows_remote": False,
    }],
}


class TestTrakstar(unittest.TestCase):
    def setUp(self):
        self.p = _registry.get("trakstar")

    def test_detect(self):
        self.assertEqual(self.p.detect("https://acme.hire.trakstar.com/").slug, "acme")
        self.assertEqual(self.p.detect("https://jsapi.recruiterbox.com/v1/openings?client_name=zed").slug, "zed")
        self.assertIsNone(self.p.detect("https://www.trakstar.com/"))
        self.assertIsNone(self.p.detect("https://example.com/"))

    def test_fetch(self):
        ctx = ctx_with({"jsapi.recruiterbox.com/v1/openings": FIXTURE})
        jobs = self.p.fetch(Target(company="Acme", slug="acme"), ctx)
        self.assertEqual(len(jobs), 1)
        j = jobs[0]
        self.assertEqual(j.title, "Support Specialist")
        self.assertEqual(j.url, "https://acme.hire.trakstar.com/jobs/fk0abc/")
        self.assertEqual(j.location, "Austin, TX, US")
        self.assertIn("users", j.description)
        self.assertEqual(j.source, "trakstar")


if __name__ == "__main__":
    unittest.main()
