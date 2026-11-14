import unittest

from tests.providers._helpers import ctx_with
from scripts.providers import _registry
from scripts.providers._base import Target

FIXTURE = {
    "jobs": [
        {
            "id": 4012345,
            "title": "Applied AI Engineer",
            "absolute_url": "https://job-boards.greenhouse.io/acme/jobs/4012345",
            "location": {"name": "Toronto, ON"},
            "offices": [{"name": "Toronto"}],
            "departments": [{"name": "Engineering"}],
            "first_published": "2026-11-01T12:00:00-04:00",
            "content": "&lt;p&gt;Build &lt;b&gt;agents&lt;/b&gt;.&lt;/p&gt;",
        }
    ]
}


class TestGreenhouse(unittest.TestCase):
    def setUp(self):
        self.p = _registry.get("greenhouse")

    def test_detect(self):
        t = self.p.detect("https://job-boards.greenhouse.io/acme")
        self.assertEqual(t.slug, "acme")
        self.assertEqual(self.p.detect("https://boards.greenhouse.io/embed/job_board?for=stripe").slug, "stripe")
        self.assertIsNone(self.p.detect("https://example.com/careers"))

    def test_fetch_normalises(self):
        ctx = ctx_with({"boards-api.greenhouse.io/v1/boards/acme/jobs": FIXTURE})
        jobs = self.p.fetch(Target(company="Acme", slug="acme"), ctx)
        self.assertEqual(len(jobs), 1)
        j = jobs[0]
        self.assertEqual(j.title, "Applied AI Engineer")
        self.assertEqual(j.company, "Acme")
        self.assertEqual(j.location, "Toronto, ON")
        self.assertIn("agents", j.description)
        self.assertTrue(j.posted_at.startswith("2026-11-01"))
        self.assertEqual(j.source, "greenhouse")


if __name__ == "__main__":
    unittest.main()
