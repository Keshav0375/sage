import unittest

from tests.providers._helpers import ctx_with
from scripts.providers import _registry
from scripts.providers._base import Target

FIXTURE = """<?xml version="1.0" encoding="UTF-8"?>
<workzag-jobs>
<position><id>1834171</id><office>Munich</office>
  <additionalOffices><office>Berlin</office></additionalOffices>
  <department>Engineering</department><employmentType>permanent</employmentType>
  <name>Staff Software Engineer, Data &amp; Platform</name>
  <createdAt>2024-11-13T14:10:41+00:00</createdAt>
  <jobDescriptions><jobDescription><name>Ignore me</name><value>x</value></jobDescription></jobDescriptions></position>
<position><id>777</id><office>Cologne</office><name></name></position>
<position><id>abc</id><office>Hamburg</office><name>Bad ID</name></position>
</workzag-jobs>"""


class TestPersonio(unittest.TestCase):
    def setUp(self):
        self.p = _registry.get("personio")

    def test_detect(self):
        t = self.p.detect("https://acme.jobs.personio.de/")
        self.assertEqual((t.slug, t.api_url), ("acme", "https://acme.jobs.personio.de/xml"))
        self.assertIsNotNone(self.p.detect("https://acme.jobs.personio.com/?language=en"))
        self.assertIsNone(self.p.detect("https://example.com/careers"))

    def test_fetch(self):
        ctx = ctx_with({"acme.jobs.personio.de/xml": FIXTURE})
        jobs = self.p.fetch(self.p.detect("https://acme.jobs.personio.de/"), ctx)
        self.assertEqual(len(jobs), 1)
        j = jobs[0]
        self.assertEqual((j.title, j.url, j.source), ("Staff Software Engineer, Data & Platform", "https://acme.jobs.personio.de/job/1834171", "personio"))
        self.assertEqual((j.location, j.department, j.employment), ("Munich | Berlin", "Engineering", "fulltime"))
        self.assertTrue(j.posted_at.startswith("2024-11-13"))


if __name__ == "__main__":
    unittest.main()

