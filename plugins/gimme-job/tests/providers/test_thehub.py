import unittest

from tests.providers._helpers import ctx_with
from scripts.providers import _registry
from scripts.providers._base import Target

FIXTURE = {"jobs": {"pages": 1, "docs": [
    {"id": "5f1a2b3c", "title": "Growth Marketer", "isRemote": True,
     "company": {"name": "Nordic Co"}, "location": {"locality": "Copenhagen", "country": "Denmark"}},
]}}


class TestTheHub(unittest.TestCase):
    def test_fetch(self):
        p = _registry.get("thehub")
        jobs = p.fetch(Target(location="DK"), ctx_with({"thehub.io/api/v2/jobsandfeatured": FIXTURE}))
        self.assertEqual(len(jobs), 1)
        j = jobs[0]
        self.assertEqual(j.url, "https://thehub.io/jobs/5f1a2b3c")
        self.assertEqual((j.company, j.location, j.workplace), ("Nordic Co", "Copenhagen, Denmark, Remote", "remote"))


if __name__ == "__main__":
    unittest.main()
