import unittest

from tests.providers._helpers import ctx_with
from scripts.providers import _registry
from scripts.providers._base import Target

RESP = {"data": [
    {"id": "11", "title": "Recruiter", "url": "https://acme.pinpointhq.com/en/postings/abc", "description": "<p>Hire people.</p>",
     "location": {"name": "", "city": "Leeds", "province": "England"}, "workplace_type": "hybrid", "employment_type": "full_time",
     "department": {"name": "People"}},
    {"id": "12", "title": "Demo", "url": "https://acme.pinpointhq.com/en/postings/demo",
     "description": "youtube.com/embed/https://www.youtube.com/embed/pFxm6fszrpw"}]}


class TestPinpoint(unittest.TestCase):
    def setUp(self):
        self.p = _registry.get("pinpoint")

    def test_detect(self):
        self.assertEqual(self.p.detect("https://acme.pinpointhq.com/").slug, "acme")
        self.assertIsNone(self.p.detect("https://example.com/careers"))

    def test_fetch(self):
        jobs = self.p.fetch(Target(company="Acme", careers_url="https://acme.pinpointhq.com"), ctx_with({"acme.pinpointhq.com/postings.json": RESP}))
        self.assertEqual(len(jobs), 1)
        j = jobs[0]
        self.assertEqual((j.title, j.location, j.workplace, j.department, j.source), ("Recruiter", "Leeds, England", "hybrid", "People", "pinpoint"))
        self.assertEqual(j.description, "Hire people.")


if __name__ == "__main__":
    unittest.main()
