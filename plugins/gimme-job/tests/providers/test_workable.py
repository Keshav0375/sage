import unittest

from tests.providers._helpers import ctx_with
from scripts.providers import _registry
from scripts.providers._base import Target

FIXTURE = {"name": "Acme Co", "jobs": [
    {"title": "Senior AI PM", "shortcode": "ABC123", "shortlink": "https://apply.workable.com/j/ABC123",
     "city": "Ghent", "country": "Belgium", "published_on": "2026-04-01", "description": "<p>Own the <b>roadmap</b>.</p>"},
    {"title": "Tech Lead", "shortlink": "https://apply.workable.com/j/DEF456", "telecommuting": True, "published_on": "2026-03-25"},
    {"title": "Tech Lead", "shortlink": "https://apply.workable.com/j/DEF456", "country": "Spain"},
    {"title": "Evil Role", "shortlink": "https://evil.example/j/X"},
    {"title": "  ", "shortlink": "https://apply.workable.com/j/NOPE"},
]}


class TestWorkable(unittest.TestCase):
    def setUp(self):
        self.p = _registry.get("workable")

    def test_detect(self):
        self.assertEqual(self.p.detect("https://apply.workable.com/acme/").slug, "acme")
        self.assertIsNone(self.p.detect("https://example.com/careers"))

    def test_fetch(self):
        ctx = ctx_with({"apply.workable.com/api/v1/widget/accounts/acme": FIXTURE})
        jobs = self.p.fetch(Target(slug="acme"), ctx)
        self.assertEqual([j.title for j in jobs], ["Senior AI PM", "Tech Lead"])
        self.assertEqual(jobs[0].company, "Acme Co")
        self.assertEqual(jobs[0].locations, ["Ghent, Belgium"])
        self.assertIn("roadmap", jobs[0].description)
        self.assertEqual(jobs[1].workplace, "remote")
        self.assertEqual(jobs[1].locations, ["Spain"])
        self.assertEqual(jobs[0].source, "workable")


if __name__ == "__main__":
    unittest.main()

