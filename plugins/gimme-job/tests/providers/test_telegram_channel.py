import json
import unittest

from tests.providers._helpers import ctx_with
from scripts.providers import _registry
from scripts.providers._base import Target

def post(pid, date, body):
    return f'''<div class="tgme_widget_message_wrap js-widget_message_wrap">
<div class="tgme_widget_message" data-post="devjobs/{pid}"><div class="tgme_widget_message_text js-message_text" dir="auto">{body}</div>
<span class="tgme_widget_message_meta"><a class="tgme_widget_message_date" href="https://t.me/devjobs/{pid}"><time datetime="{date}" class="time">1</time></a></span></div></div>'''


A = lambda h: f'<a href="{h}">{h}</a>'
RECENT = "2099-01-01T10:00:00+00:00"
PAGE = "<html><body>" + "".join([
    post(12509, RECENT, f"MLOps Engineer, senior<br/>#remote<br/>Компания: Контур<br/>Apply: {A('https://kontur.ru/career/vacancy/12345?utm_source=tg')}"),
    post(12508, RECENT, f"Data Engineer @ Ostrovok<br/>{A('https://getmatch.ru/vacancies/33927-data-engineer?s=bot')}"),
    post(12507, RECENT, "Hiring a designer | Nexters<br/>Write to @hr"),
    post(12506, RECENT, f"Backend Dev | Acme Studio<br/>{A('https://forms.gle/xyz')}"),
    post(12505, "2020-01-01T10:00:00+00:00", f"Old Role @ OldCo<br/>{A('https://oldco.com/jobs/123456')}"),
]) + "</body></html>"
NO_PREVIEW = '<html><head><meta property="og:title" content="Telegram: Contact @gophersjob"></head></html>'


class TestTelegramChannel(unittest.TestCase):
    def setUp(self):
        self.p = _registry.get("telegram-channel")

    def test_detect(self):
        self.assertEqual(self.p.detect("https://t.me/s/devjobs").options["channel"], "devjobs")
        self.assertIsNone(self.p.detect("https://example.com/devjobs"))

    def test_fetch_policy(self):
        jobs = self.p.fetch(Target(options={"channel": "devjobs"}), ctx_with({"t.me/s/devjobs": PAGE}))
        self.assertEqual([(j.title, j.company) for j in jobs],
                         [("MLOps Engineer, senior", "Контур"), ("Data Engineer @ Ostrovok", "Ostrovok")])
        self.assertEqual(jobs[0].url, "https://kontur.ru/career/vacancy/12345?utm_source=tg")
        self.assertIn("Source: https://t.me/devjobs/12509", jobs[0].description)
        self.assertEqual(jobs[1].url, "https://getmatch.ru/vacancies/33927-data-engineer?s=bot")

    def test_no_preview(self):
        from scripts.providers._base import ProviderError
        with self.assertRaises(ProviderError):
            self.p.fetch(Target(options={"channel": "gophersjob"}), ctx_with({"t.me/s/gophersjob": NO_PREVIEW}))


if __name__ == "__main__":
    unittest.main()
