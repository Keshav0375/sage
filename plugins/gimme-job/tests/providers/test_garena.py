import unittest

from tests.providers._helpers import ctx_with
from scripts.providers import _registry
from scripts.providers._base import Target

FIXTURE = {"jobs": [{"id": 4321, "title": "Game Designer", "tags": {"location": ["Singapore", "Jakarta"]},
                     "description": "<p>Design <b>games</b></p>"}]}


class TestGarena(unittest.TestCase):
    def setUp(self):
        self.p = _registry.get("garena")

    def test_detect(self):
        self.assertIsNotNone(self.p.detect("https://careers.garena.com/global"))
        self.assertIsNone(self.p.detect("https://example.com/"))

    def test_fetch(self):
        ctx = ctx_with({"careers.garena.com/api/job/list": FIXTURE})
        jobs = self.p.fetch(Target(), ctx)
        self.assertEqual(len(jobs), 1)
        j = jobs[0]
        self.assertEqual(j.url, "https://careers.garena.com/global/careers/4321")
        self.assertEqual(j.locations, ["Singapore", "Jakarta"])
        self.assertIn("games", j.description)
        self.assertEqual(j.company, "Garena")
        self.assertEqual(j.source, "garena")


if __name__ == "__main__":
    unittest.main()
