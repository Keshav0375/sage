import unittest

from tests.providers._helpers import ctx_with
from scripts.providers._base import Target
from scripts.providers.itviec import PROVIDER

CARD = '''<div class='job-card' data-search--job-selection-job-slug-value='senior-backend-engineer-fundiin-5621' data-x='0'>
  <span class='small-text'>Posted
  1 day ago
  </span>
  <h3 class='imt-3' data-controller='utm-tracking' data-search--job-selection-target='jobTitle'>
    <a target="_blank" href="https://itviec.com/it-jobs/senior-backend-engineer-fundiin-5621?x=1">Back &amp; Middle End Engineer</a>
  </h3>
  <a title="FUNDIIN" class="logo" href="/companies/fundiin?x=1"><picture></picture></a>
  <span><a class="text-rich-grey" href="/companies/fundiin?x=1">Fundiin</a></span>
  <svg><use href="https://itviec.com/assets/feather-icons-sprite.svg#map-pin"></use></svg>
  <div class='text-truncate' title='Ho Chi Minh'>Ho Chi Minh</div>
</div>
<div class='job-card' data-search--job-selection-job-slug-value='middle-java-0508'>
  <h3 data-search--job-selection-target='jobTitle'><a href="/it-jobs/middle-java-0508">Middle Java Developer</a></h3>
</div>'''


class TestITviec(unittest.TestCase):
    def test_fetch(self):
        jobs = PROVIDER.fetch(Target(query="backend"), ctx_with({"itviec.com/it-jobs/backend": CARD}))
        self.assertEqual(len(jobs), 2)
        a, b = jobs
        self.assertEqual((a.title, a.company, a.location), ("Back & Middle End Engineer", "Fundiin", "Ho Chi Minh"))
        self.assertEqual(a.url, "https://itviec.com/it-jobs/senior-backend-engineer-fundiin-5621")
        self.assertTrue(a.posted_at)
        self.assertEqual((b.company, b.location, b.posted_at), ("", "", ""))


if __name__ == "__main__":
    unittest.main()
