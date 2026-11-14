import unittest

from tests.providers._helpers import ctx_with
from scripts.providers import _registry
from scripts.providers._base import Target

FIXTURE = {"meta": {"totalCount": 2}, "result": [
    {"id": "37", "jobOpeningName": "Support Specialist", "departmentLabel": "Support",
     "employmentStatusLabel": "Full-Time", "location": {"city": "Lindon", "state": "Utah"}, "isRemote": False},
    {"id": "38", "jobOpeningName": "Designer", "location": {"city": None, "state": None}, "isRemote": True},
    {"id": "", "jobOpeningName": "No id"},
]}


class TestBambooHR(unittest.TestCase):
    def setUp(self):
        self.p = _registry.get("bamboohr")

    def test_detect(self):
        self.assertEqual(self.p.detect("https://acme.bamboohr.com/careers").slug, "acme")
        self.assertIsNone(self.p.detect("https://example.com/careers"))

    def test_fetch(self):
        ctx = ctx_with({"acme.bamboohr.com/careers/list": FIXTURE})
        jobs = self.p.fetch(self.p.detect("https://acme.bamboohr.com/careers"), ctx)
        self.assertEqual(len(jobs), 2)
        self.assertEqual(jobs[0].url, "https://acme.bamboohr.com/careers/37")
        self.assertEqual((jobs[0].title, jobs[0].location, jobs[0].employment, jobs[0].source), ("Support Specialist", "Lindon, Utah", "fulltime", "bamboohr"))
        self.assertEqual((jobs[1].location, jobs[1].workplace), ("Remote", "remote"))


if __name__ == "__main__":
    unittest.main()

