import unittest

from tests.providers._helpers import ctx_with
from scripts.providers import _registry
from scripts.providers._base import Target

HTML = """
<div data-target='job-filters.officeGroup'>
  <h3 class="x">Barcelona</h3>
  <ul>
  <li class='job-offer-item a' data-is-remote='false'
      data-job-postings-url='https://acme.factorial.com/job_posting/account-executive-123'>
    <div class="x factorial__headingFontFamily">Account Executive</div>
  </li>
  <li class='job-offer-item a' data-is-remote='true'
      data-job-postings-url='https://acme.factorial.com/job_posting/sdr-456'>
    <div class="x factorial__headingFontFamily">SDR &amp; Growth</div>
  </li>
  <li class='job-offer-item a' data-is-remote='false'
      data-job-postings-url='https://other.factorial.com/job_posting/x-9'>
    <div class="x factorial__headingFontFamily">Foreign</div>
  </li>
  </ul>
</div>
"""


class TestFactorial(unittest.TestCase):
    def setUp(self):
        self.p = _registry.get("factorial")

    def test_detect(self):
        self.assertEqual(self.p.detect("https://acme.factorialhr.com").api_url, "https://acme.factorial.com/")
        self.assertIsNone(self.p.detect("https://www.factorialhr.com"))
        self.assertIsNone(self.p.detect("https://example.com"))

    def test_fetch(self):
        ctx = ctx_with({"acme.factorial.com/": HTML})
        jobs = self.p.fetch(Target(company="Acme", careers_url="https://acme.factorialhr.com"), ctx)
        self.assertEqual([j.title for j in jobs], ["Account Executive", "SDR & Growth"])
        self.assertEqual(jobs[0].url, "https://acme.factorial.com/job_posting/account-executive-123")
        self.assertEqual(jobs[0].location, "Barcelona")
        self.assertEqual(jobs[1].location, "Barcelona · Remote")
        self.assertEqual(jobs[1].source_id, "456")
        self.assertEqual(jobs[0].source, "factorial")


if __name__ == "__main__":
    unittest.main()
