import unittest

from tests.providers._helpers import ctx_with
from scripts.providers import _registry
from scripts.providers._base import Target

SITE = "ABCDEFGHIJ1234567890"
PAGE = ('<html><div data-talentlink-fo-host="emea3.recruitmentplatform.com" '
        'data-talentlink-fo-site-tech-id="%s"></div></html>' % SITE)
CRITERIA = {"LOV1": {"lovName": "Location", "items": [{"value": 1, "label": "Paris"}]},
            "LOV2": {"lovName": "Function", "items": []}}
JOBS = {"globals": {"jobsCount": 1}, "jobs": [{
    "id": 123456, "jobFields": {"jobTitle": "Data Scientist", "SLOVLIST1": "Paris", "SLOVLIST2": "Tech",
                                "DPOSTINGSTART": 1760000000000, "WorkMode": ["Hybrid"]},
    "customFields": [{"title": "Mission", "content": "<p>Model <b>things</b></p>"}],
}]}


class TestTalentLink(unittest.TestCase):
    def setUp(self):
        self.p = _registry.get("talentlink")

    def test_detect(self):
        self.assertIsNotNone(self.p.detect("https://acme.recruitmentplatform.com/syndicated/index.html"))
        self.assertIsNone(self.p.detect("https://example.com/careers"))

    def test_fetch(self):
        ctx = ctx_with({
            "acme.recruitmentplatform.com/index.html": PAGE,
            "/fo/rest/config": {"navigationPages": {"jobDescriptionURL": "details.html"}},
            "/fo/rest/jobs/criteria": CRITERIA,
            "/fo/rest/jobs?": JOBS,
        })
        jobs = self.p.fetch(Target(company="Acme", careers_url="https://acme.recruitmentplatform.com/"), ctx)
        self.assertEqual(len(jobs), 1)
        j = jobs[0]
        self.assertEqual(j.title, "Data Scientist")
        self.assertEqual(j.url, "https://acme.recruitmentplatform.com/details.html?jobId=123456")
        self.assertEqual(j.location, "Paris")
        self.assertEqual(j.workplace, "hybrid")
        self.assertIn("things", j.description)
        self.assertEqual(j.source, "talentlink")


if __name__ == "__main__":
    unittest.main()
