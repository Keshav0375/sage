import unittest

from tests.providers._helpers import ctx_with
from scripts.providers import _registry
from scripts.providers._base import Target

URL = "https://hr.acme.edu/psc/exu1/EMPLOYEE/HRMS/c/HRS_HRAM_FL.HRS_CG_SEARCH_FL.GBL?Page=HRS_APP_SCHJOB_FL&Action=U"
PAGE = """<html><form name="win0" action="/psc/exu1/EMPLOYEE/HRMS/c/HRS_HRAM_FL.HRS_CG_SEARCH_FL.GBL"><input type="hidden" name="ICStateNum" value="3"/>
<div id="win0divHRS_AGNT_RSLT_Irowcnt$0"><span>1 of 1</span></div>
<ul><li id="HRS_AGNT_RSLT_I$0_row_0"><span id="SCH_JOB_TITLE$0">Research Coordinator</span>
<span id="HRS_APP_JBSCH_I_HRS_JOB_OPENING_ID$0">123456</span><span id="LOCATION$0">Main Campus</span>
<span id="HRS_APP_JBSCH_I_HRS_DEPT_DESCR$0">Biology</span><span id="SCH_OPENED$0">11/03/2026</span></li></ul></form></html>"""


class TestPeopleSoft(unittest.TestCase):
    def setUp(self):
        self.p = _registry.get("peoplesoft")

    def test_detect(self):
        self.assertEqual(self.p.detect(URL).slug, "exu1")
        self.assertIsNone(self.p.detect("https://example.com/careers"))

    def test_fetch(self):
        jobs = self.p.fetch(Target(company="Acme U", careers_url=URL), ctx_with({"HRS_CG_SEARCH_FL.GBL": PAGE}))
        self.assertEqual(len(jobs), 1)
        j = jobs[0]
        self.assertEqual((j.title, j.location, j.department, j.posted_at, j.source),
                         ("Research Coordinator", "Main Campus", "Biology", "2026-11-03", "peoplesoft"))
        self.assertIn("JobOpeningId=123456", j.url)


if __name__ == "__main__":
    unittest.main()
