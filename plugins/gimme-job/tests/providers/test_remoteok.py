import unittest

from tests.providers._helpers import ctx_with
from scripts.providers import _registry
from scripts.providers._base import Target

FIXTURE = [
    {"legal": "RemoteOK terms"},
    {"id": "9001", "position": "Rust Developer", "company": "Ferrous", "location": "Worldwide",
     "url": "https://remoteok.com/remote-jobs/9001", "date": "2026-11-01T08:00:00+00:00",
     "tags": ["rust", "backend"], "description": "<p>Write <b>Rust</b>.</p>", "salary_min": 90000, "salary_max": 140000},
    {"id": "9002", "position": "Support Agent", "company": "Helpful", "url": "https://remoteok.com/remote-jobs/9002", "tags": ["support"]},
]


class TestRemoteOK(unittest.TestCase):
    def setUp(self):
        self.p = _registry.get("remoteok")

    def test_detect_none(self):
        self.assertIsNone(self.p.detect("https://remoteok.com/"))

    def test_fetch(self):
        jobs = self.p.fetch(Target(), ctx_with({"remoteok.com/api": FIXTURE}))
        self.assertEqual(len(jobs), 2)
        j = jobs[0]
        self.assertEqual((j.title, j.company, j.location, j.workplace, j.source), ("Rust Developer", "Ferrous", "Worldwide", "remote", "remoteok"))
        self.assertEqual((j.salary_min, j.salary_max), (90000, 140000))
        self.assertIn("Rust", j.description)

    def test_query(self):
        jobs = self.p.fetch(Target(query="rust"), ctx_with({"remoteok.com/api": FIXTURE}))
        self.assertEqual([j.source_id for j in jobs], ["9001"])


if __name__ == "__main__":
    unittest.main()

