import unittest

from tests.providers._helpers import ctx_with
from scripts.providers import _registry
from scripts.providers._base import Target

BODY = r"""function applyFor(id){}
document.write('<table class=\'title\'><tr><td id=\'wrapword\' class=\'x\'>Math Teacher &amp; Coach</td><td>JobID: 3141</td></tr></table>
<span class=\"label\">Location:</span> <span class=\"normal\">Lincoln High School</span>
<span class=\"label\">Date Posted:</span> <span class=\"normal\">9/21/2026</span>');
document.write('<table class=\'title\'><tr><td id=\'wrapword\'>Bus Driver</td><td>JobID: 2718</td></tr></table>');"""


class TestAppliTrack(unittest.TestCase):
    def setUp(self):
        self.p = _registry.get("applitrack")

    def test_detect(self):
        t = self.p.detect("https://www.applitrack.com/Acme/onlineapp/default.aspx?all=1")
        self.assertEqual(t.slug, "acme")
        self.assertIsNone(self.p.detect("https://example.com/acme"))
        self.assertIsNone(self.p.detect("http://www.applitrack.com/acme/"))

    def test_fetch(self):
        ctx = ctx_with({"applitrack.com/acme/onlineapp/jobpostings/Output.asp": BODY})
        jobs = self.p.fetch(Target(company="Acme USD", slug="acme", options={"default_location": "Springfield, IL"}), ctx)
        self.assertEqual([j.title for j in jobs], ["Math Teacher & Coach", "Bus Driver"])
        j = jobs[0]
        self.assertEqual(j.url, "https://www.applitrack.com/acme/onlineapp/default.aspx?AppliTrackJobId=3141&AppliTrackLayoutMode=detail&AppliTrackViewPosting=1")
        self.assertEqual(j.location, "Lincoln High School - Springfield, IL")
        self.assertEqual(j.posted_at, "2026-09-21")
        self.assertEqual(j.source, "applitrack")


if __name__ == "__main__":
    unittest.main()
