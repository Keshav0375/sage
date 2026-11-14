import json
import unittest

from tests.providers._helpers import ctx_with
from scripts.providers import _registry
from scripts.providers._base import Target

POSTINGS = [{
    "id": "abc-123", "title": "Backend Engineer", "richtextDescription": "$1a",
    "createdAt": "2026-10-01T00:00:00Z",
    "job": {"workArrangementEnum": "REMOTE",
            "jobLocations": [{"location": {"name": "Berlin", "country": {"name": "Germany"}}}]},
    "jobPostingPublications": [{"currentState": {"stateSlug": "published", "createdAt": "2026-10-05T00:00:00Z"}}],
}]
DESC = "<p>Build services</p>"


def page():
    chunk1 = '0:["$","div",null,{"jobPostings":' + json.dumps(POSTINGS) + "}]\n"
    chunk2 = "1a:T%x,%s\n" % (len(DESC.encode()), DESC)
    pushes = "".join('<script>self.__next_f.push([1,%s])</script>' % json.dumps(c) for c in (chunk1, chunk2))
    return "<html><head><title>Acme</title></head><body>" + pushes + "</body></html>"


class TestDeel(unittest.TestCase):
    def setUp(self):
        self.p = _registry.get("deel")

    def test_detect(self):
        self.assertEqual(self.p.detect("https://jobs.deel.com/klarna").slug, "klarna")
        self.assertIsNone(self.p.detect("https://example.com/klarna"))

    def test_fetch(self):
        ctx = ctx_with({"jobs.deel.com/acme": page()})
        jobs = self.p.fetch(Target(company="Acme", slug="acme"), ctx)
        self.assertEqual(len(jobs), 1)
        j = jobs[0]
        self.assertEqual(j.title, "Backend Engineer")
        self.assertEqual(j.url, "https://jobs.deel.com/acme/job-details/abc-123/overview")
        self.assertEqual(j.location, "Berlin, Germany; Remote")
        self.assertEqual(j.workplace, "remote")
        self.assertTrue(j.posted_at.startswith("2026-10-05"))
        self.assertIn("Build services", j.description)
        self.assertEqual(j.source, "deel")


if __name__ == "__main__":
    unittest.main()
