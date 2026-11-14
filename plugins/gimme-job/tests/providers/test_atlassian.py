import json
import unittest

from tests.providers._helpers import ctx_with
from scripts.providers import _registry
from scripts.providers._base import Target

FIXTURE = [{"id": 7654, "title": "Senior Product Manager", "locations": ["Sydney,  Australia", "Remote - US"],
            "category": "Product", "portalJobPost": {"portalUrl": "https://www.atlassian.com/company/careers/details/7654"}},
           {"id": 1, "title": "No url"}]


class TestAtlassian(unittest.TestCase):
    def test_detect(self):
        p = _registry.get("atlassian")
        self.assertIsNotNone(p.detect("https://www.atlassian.com/company/careers"))
        self.assertIsNone(p.detect("https://www.atlassian.com/software/jira"))

    def test_fetch(self):
        jobs = _registry.get("atlassian").fetch(Target(), ctx_with({"atlassian.com/endpoint/careers/listings": FIXTURE}))
        self.assertEqual(len(jobs), 1)
        j = jobs[0]
        self.assertEqual((j.title, j.company, j.location), ("Senior Product Manager", "Atlassian", "Sydney, Australia; Remote - US"))
        self.assertEqual(j.url, "https://www.atlassian.com/company/careers/details/7654")


if __name__ == "__main__":
    unittest.main()
