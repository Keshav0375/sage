import json
import unittest

from tests.providers._helpers import ctx_with
from scripts.providers import _registry
from scripts.providers._base import Target

FIXTURE = {"jobs": [
    {"public_id": "abc123", "title": "Support Engineer", "location": "EMEA, NORAM", "workplace": "remote", "opened_at": "2026-10-30T08:00:00Z"},
    {"public_id": "zzz", "title": "Closed", "status": "closed"}]}


class TestRemoteCom(unittest.TestCase):
    def test_detect(self):
        p = _registry.get("remote-com")
        self.assertIsNotNone(p.detect("https://apply.remote.com/"))
        self.assertIsNone(p.detect("https://example.com/careers"))

    def test_fetch(self):
        jobs = _registry.get("remote-com").fetch(Target(), ctx_with({"apply.remote.com/api/public/jobs": FIXTURE}))
        self.assertEqual(len(jobs), 1)
        j = jobs[0]
        self.assertEqual(j.url, "https://apply.remote.com/jobs/abc123")
        self.assertEqual(j.company, "Remote")
        self.assertEqual(j.location, "Remote · EMEA (Europe, Middle East & Africa) / NORAM (North America)")
        self.assertEqual(j.workplace, "remote")


if __name__ == "__main__":
    unittest.main()
