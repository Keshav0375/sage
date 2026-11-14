import unittest

from tests.providers._helpers import ctx_with
from scripts.providers import _registry
from scripts.providers._base import Target

FIXTURE = {"data": {"next_page_url": None, "data": [
    {"id": 3, "title": "Marketing Manager", "urlJobApplay": "https://flowxtra.com/apply/abc",
     "name_company": "Beispiel GmbH", "city_company": "Berlin", "country_company": "Germany",
     "workplace": "Remote", "date_share": "2026-10-08T09:00:00Z"},
    {"id": 4, "title": "Offsite", "urlJobApplay": "https://evil.example/apply/x"},
]}}


class TestFlowxtra(unittest.TestCase):
    def setUp(self):
        self.p = _registry.get("flowxtra")

    def test_detect_none(self):
        self.assertIsNone(self.p.detect("https://flowxtra.com/"))

    def test_fetch(self):
        ctx = ctx_with({"app.flowxtra.com/api/central/jobs": FIXTURE})
        jobs = self.p.fetch(Target(), ctx)
        self.assertEqual(len(jobs), 1)
        j = jobs[0]
        self.assertEqual(j.title, "Marketing Manager")
        self.assertEqual(j.url, "https://flowxtra.com/apply/abc")
        self.assertEqual(j.company, "Beispiel GmbH")
        self.assertEqual(j.location, "Berlin, Germany, Remote")
        self.assertEqual(j.workplace, "remote")
        self.assertEqual(j.source, "flowxtra")


if __name__ == "__main__":
    unittest.main()
