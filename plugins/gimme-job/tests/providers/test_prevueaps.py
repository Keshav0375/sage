import unittest

from tests.providers._helpers import ctx_with
from scripts.providers import _registry
from scripts.providers._base import Target

PAGE = '<html><script>fetch("/core/jobs/4711?getParams=...")</script></html>'
API = {"success": True, "data": {"jobCount": 1, "jobs": [{
    "title": "Registered Nurse", "jobUrl": "https://acme.prevueaps.ca/jobs/88",
    "jobLocation": "Calgary, AB", "employmentType": "Full-Time", "classification": "Nursing",
    "minSalary": "$40", "maxSalary": "$55", "payTypeFrame": "per hour",
}]}}


class TestPrevueaps(unittest.TestCase):
    def setUp(self):
        self.p = _registry.get("prevueaps")

    def test_detect(self):
        self.assertEqual(self.p.detect("https://acme.prevueaps.ca/jobs/").slug, "acme")
        self.assertIsNone(self.p.detect("https://example.com/jobs/"))

    def test_fetch(self):
        ctx = ctx_with({"/core/jobs/4711": API, "acme.prevueaps.ca/jobs/": PAGE})
        jobs = self.p.fetch(Target(company="Acme", careers_url="https://acme.prevueaps.ca/jobs/"), ctx)
        self.assertEqual(len(jobs), 1)
        j = jobs[0]
        self.assertEqual(j.title, "Registered Nurse")
        self.assertEqual(j.url, "https://acme.prevueaps.ca/jobs/88")
        self.assertEqual(j.location, "Calgary, AB")
        self.assertIn("Full-Time", j.description)
        self.assertEqual(j.source, "prevueaps")


if __name__ == "__main__":
    unittest.main()
