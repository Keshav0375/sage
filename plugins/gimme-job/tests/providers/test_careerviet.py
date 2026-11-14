import unittest

from tests.providers._helpers import ctx_with
from scripts.providers._base import Target
from scripts.providers.careerviet import PROVIDER

PAGE = '''<div class="job-item  " id="job-item-35C82AFA"><div class="figcaption"><div class="title "><h2><a class="job_link" data-id="35C82AFA" target="_blank" title="Backend Developer &amp; API" rel="noopener" href="/vi/tim-viec-lam/backend-developer.35C82AFA.html">Backend Developer &amp; API</a></h2></div><div class="caption"><a class="company-name" target="_blank" title="CONG TY CC1" href="/vi/nha-tuyen-dung/cc1.html">CONG TY CC1</a><a class="job_link" title="Backend Developer &amp; API" href="/vi/tim-viec-lam/backend-developer.35C82AFA.html"><div class="location"><em></em><ul><li>Ho Chi Minh</li></ul></div><div class="time"><ul><li><span>Han nop: </span><time>10-09-2026</time></li><li><span>Cập nhật<!-- -->:</span> <time>16-08-2026</time></li></ul></div></a></div></div></div>
<div class="job-item  " id="job-item-35C90001"><div class="title "><h2><a class="job_link" title="Middle Java Developer" href="/vi/tim-viec-lam/middle-java-developer.35C90001.html">Middle Java Developer</a></h2></div></div>'''


class TestCareerViet(unittest.TestCase):
    def test_fetch(self):
        jobs = PROVIDER.fetch(Target(query="developer"), ctx_with({"developer-k-vi.html": PAGE, "trang-2": "<html></html>"}))
        self.assertEqual(len(jobs), 2)
        a, b = jobs
        self.assertEqual((a.title, a.company, a.location, a.posted_at), ("Backend Developer & API", "CONG TY CC1", "Ho Chi Minh", "2026-08-16"))
        self.assertEqual(a.url, "https://careerviet.vn/vi/tim-viec-lam/backend-developer.35C82AFA.html")
        self.assertEqual((b.company, b.location, b.posted_at), ("", "", ""))


if __name__ == "__main__":
    unittest.main()
