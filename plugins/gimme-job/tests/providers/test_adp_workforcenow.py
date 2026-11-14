import unittest

from tests.providers._helpers import ctx_with
from scripts.providers import _registry
from scripts.providers._base import Target

URL = "https://workforcenow.adp.com/mascsr/default/mdf/recruitment/recruitment.html?cid=abc-123&ccId=19000101_000001&lang=en_US"
RESP = {"meta": {"totalNumber": 1}, "jobRequisitions": [{
    "itemID": "900123456", "requisitionTitle": "Dispatcher", "postDate": "2026-11-03T12:00:00.000Z",
    "requisitionLocations": [{"nameCode": {"shortName": "Mesa, AZ"}}],
    "payGradeRange": {"minimumRate": {"amountValue": 50000, "currencyCode": "USD"}, "maximumRate": {"amountValue": 65000, "currencyCode": "USD"}},
    "customFieldGroup": {"stringFields": [{"nameCode": {"codeValue": "ExternalJobID"}, "stringValue": "EXT-9"}]}}]}


class TestAdpWorkforceNow(unittest.TestCase):
    def setUp(self):
        self.p = _registry.get("adp-workforcenow")

    def test_detect(self):
        self.assertEqual(self.p.detect(URL).slug, "abc-123")
        self.assertIsNone(self.p.detect("https://workforcenow.adp.com/other"))
        self.assertIsNone(self.p.detect("https://example.com/careers"))

    def test_fetch(self):
        jobs = self.p.fetch(Target(company="Acme", careers_url=URL), ctx_with({"staffing/v1/job-requisitions": RESP}))
        self.assertEqual(len(jobs), 1)
        j = jobs[0]
        self.assertEqual((j.title, j.location, j.salary_min, j.salary_max, j.currency, j.source),
                         ("Dispatcher", "Mesa, AZ", 50000, 65000, "USD", "adp-workforcenow"))
        self.assertIn("jobId=EXT-9", j.url)
        self.assertIn("jwId=900123456", j.url)


if __name__ == "__main__":
    unittest.main()
