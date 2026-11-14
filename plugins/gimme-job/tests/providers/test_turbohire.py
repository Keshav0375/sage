import json
import unittest

from tests.providers._helpers import ctx_with
from scripts.providers import _registry
from scripts.providers._base import Target

ORG = "0a1b2c3d-1111-2222-3333-444455556666"
JOBS = {"Total": 1, "Result": [{
    "JobTitle": "Software &amp; Data Engineer", "JobIdObfuscated": "abc%2Fdef%3D", "JobCode": "TH-1",
    "Location": json.dumps([{"Address": "Bengaluru, Karnataka"}]),
    "PublishedDate": "2026-10-06T10:00:00Z", "JobDescV2": "<p>Write <b>code</b></p>",
    "ShowClientName": True, "ClientName": "Acme Labs",
}]}


class TestTurboHire(unittest.TestCase):
    def setUp(self):
        self.p = _registry.get("turbohire")

    def test_detect(self):
        self.assertEqual(self.p.detect("https://acme.turbohire.co/").slug, "acme")
        self.assertIsNone(self.p.detect("https://app.turbohire.co/"))
        self.assertIsNone(self.p.detect("https://example.com/"))

    def test_fetch(self):
        ctx = ctx_with({
            "/api/token/noauth": {"access_token": "tkn"},
            "/api/publicorganizations": {"OrgID": ORG},
            "/api/careerpagev2/filteredjobs": JOBS,
        })
        jobs = self.p.fetch(Target(company="Acme", slug="acme"), ctx)
        self.assertEqual(len(jobs), 1)
        j = jobs[0]
        self.assertEqual(j.title, "Software & Data Engineer")
        self.assertEqual(j.url, "https://acme.turbohire.co/job/publicjobs/abc%2Fdef%3D")
        self.assertEqual(j.location, "Bengaluru, Karnataka")
        self.assertEqual(j.company, "Acme Labs")
        self.assertIn("code", j.description)
        self.assertEqual(j.source, "turbohire")


if __name__ == "__main__":
    unittest.main()
