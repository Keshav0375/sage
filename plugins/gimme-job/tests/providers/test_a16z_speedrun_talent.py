import json
import unittest

from tests.providers._helpers import ctx_with
from scripts.providers import _registry
from scripts.providers._base import Target

FIXTURE = {"jobs": [{
    "id": 991, "title": "Founding Engineer", "company": "Stealth", "url": "https://speedrun-talent-network.com/jobs/991",
    "location": "San Francisco, CA", "remote": True, "published_at": "2026-11-02T09:00:00Z"},
    {"id": 992, "title": "Off host", "company": "X", "url": "https://evil.example/jobs/1"}],
    "total": 2, "page": 0, "page_size": 50, "total_pages": 1}


class TestSpeedrun(unittest.TestCase):
    def test_fetch(self):
        p = _registry.get("a16z-speedrun-talent")
        ctx = ctx_with({"speedrun-talent-network.com/api/v1/jobs": FIXTURE})
        jobs = p.fetch(Target(query="engineer"), ctx)
        self.assertEqual(len(jobs), 1)
        j = jobs[0]
        self.assertEqual((j.title, j.company, j.location), ("Founding Engineer", "Stealth", "San Francisco, CA, Remote"))
        self.assertEqual(j.workplace, "remote")
        self.assertEqual(j.source_id, "991")
        self.assertIn("q=engineer", ctx.http.transport.calls[-1][1])


if __name__ == "__main__":
    unittest.main()
