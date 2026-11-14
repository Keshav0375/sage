import unittest

from tests.providers._helpers import ctx_with
from scripts.providers import _registry
from scripts.providers._base import Target

FIXTURE = {"success": True, "value": {"page": 1, "size": 100, "jobsList": [
    {"jobId": 777, "employer": "Hudson&#x27;s District", "title": "Grade 5 &#8211; Teacher",
     "location": "Hudson, NH", "displayDate": "2026-10-05T09:30:00"}]}}


class TestSchoolSpring(unittest.TestCase):
    def setUp(self):
        self.p = _registry.get("schoolspring")

    def test_detect(self):
        t = self.p.detect("https://hudson.schoolspring.com/")
        self.assertEqual(t.slug, "hudson")
        self.assertIsNone(self.p.detect("https://www.schoolspring.com/"))
        self.assertIsNone(self.p.detect("https://example.com/"))

    def test_fetch(self):
        ctx = ctx_with({"api.schoolspring.com/api/Jobs/GetPagedJobsWithSearch": FIXTURE})
        jobs = self.p.fetch(Target(careers_url="https://hudson.schoolspring.com/"), ctx)
        self.assertEqual(len(jobs), 1)
        j = jobs[0]
        self.assertEqual(j.title, "Grade 5 – Teacher")
        self.assertEqual(j.url, "https://hudson.schoolspring.com/?jobid=777")
        self.assertEqual(j.company, "Hudson's District")
        self.assertEqual(j.location, "Hudson, NH")
        self.assertEqual(j.source, "schoolspring")


if __name__ == "__main__":
    unittest.main()
