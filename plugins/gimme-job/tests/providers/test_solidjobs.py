import unittest

from tests.providers._helpers import ctx_with
from scripts.providers import _registry
from scripts.providers._base import Target

FIXTURE = {"jobs": [
    {"title": "Java Developer", "url": "https://solid.jobs/offer/12345/java-developer", "company": "Acme",
     "locations": ["Warszawa", "Remote"]},
    {"title": "No url", "company": "X"},
]}


class TestSolidJobs(unittest.TestCase):
    def test_fetch(self):
        p = _registry.get("solidjobs")
        ctx = ctx_with({"solid.jobs/public-api/offers/it": FIXTURE})
        jobs = p.fetch(Target(), ctx)
        self.assertEqual(len(jobs), 1)
        self.assertEqual((jobs[0].title, jobs[0].company, jobs[0].location), ("Java Developer", "Acme", "Warszawa | Remote"))
        self.assertEqual(jobs[0].source, "solidjobs")


if __name__ == "__main__":
    unittest.main()
