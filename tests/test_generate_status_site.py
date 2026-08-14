import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
GENERATOR = REPOSITORY_ROOT / "scripts" / "generate_status_site.py"
VALID_REPORT_ID = "08c2d932-ec3a-436c-336f-08def9c4406b"
SECOND_REPORT_ID = "54310359-6bf6-42c9-02bc-08de5f5e0c4a"


class GenerateStatusSiteTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.work_dir = Path(self.temp_dir.name)
        self.status_dir = self.work_dir / "status"
        self.status_dir.mkdir()

        fixtures = [
            {"name": "Compliant", "vendor": "Vendor", "slug": "compliant", "status": "compliant", "details": "Probe response is compliant", "probe_url": "https://example.com/probe", "report_id": VALID_REPORT_ID},
            {"name": "Non-compliant", "vendor": "Vendor", "slug": "non-compliant", "status": "non-compliant", "details": "Errors found", "probe_url": "https://example.net/probe", "report_id": SECOND_REPORT_ID},
            {"name": "Unreachable", "vendor": "Vendor", "slug": "unreachable", "status": "unreachable", "details": "No response", "report_id": VALID_REPORT_ID},
            {"name": "API error", "vendor": "Vendor", "slug": "api-error", "status": "error", "details": "HTTP 500", "report_id": SECOND_REPORT_ID},
            {"name": "Malformed", "vendor": "Vendor", "slug": "malformed", "status": "compliant", "details": "Bad report ID", "report_id": "not-a-uuid"},
            {"name": '<script>alert("x")</script>', "vendor": 'Bad <b>vendor</b>', "slug": "legacy", "status": "compliant", "details": '<img src=x onerror="alert(1)">', "probe_url": 'https://example.org/?x=" onmouseover="bad"'},
        ]
        for index, fixture in enumerate(fixtures):
            (self.status_dir / f"{index}.json").write_text(json.dumps(fixture), encoding="utf-8")

        subprocess.run([sys.executable, str(GENERATOR)], cwd=self.work_dir, check=True)
        self.site_dir = self.work_dir / "site"
        self.page = (self.site_dir / "index.html").read_text(encoding="utf-8")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_native_reports_are_only_rendered_for_valid_completed_reports(self):
        self.assertEqual(self.page.count("/badges/reports/"), 2)
        self.assertEqual(self.page.count('class="report-details"'), 2)
        self.assertEqual(self.page.count("Validation report unavailable"), 4)
        self.assertIn(f"/{VALID_REPORT_ID}?utm_source=github&amp;utm_medium=badge&amp;utm_campaign=mtconnect_validation", self.page)

    def test_iframe_is_deferred_and_keeps_security_attributes(self):
        self.assertEqual(self.page.count("data-src=\"https://validator.tams.ai/embed/reports/"), 2)
        self.assertNotIn('<iframe\n            src="https://validator.tams.ai/embed/reports/', self.page)
        self.assertIn('loading="lazy"', self.page)
        self.assertIn('referrerpolicy="strict-origin-when-cross-origin"', self.page)
        self.assertIn('sandbox="allow-scripts allow-popups allow-popups-to-escape-sandbox"', self.page)
        self.assertIn('frame.setAttribute("src", frame.dataset.src)', self.page)
        self.assertIn('frame.removeAttribute("data-src")', self.page)

    def test_status_content_is_html_escaped(self):
        self.assertNotIn("<script>alert", self.page)
        self.assertNotIn("<img src=x", self.page)
        self.assertIn("&lt;script&gt;alert", self.page)
        self.assertIn("Bad &lt;b&gt;vendor&lt;/b&gt;", self.page)
        self.assertIn("&quot; onmouseover=&quot;bad&quot;", self.page)

    def test_summary_and_stable_badges_remain_available(self):
        summary = json.loads((self.site_dir / "summary.json").read_text(encoding="utf-8"))
        self.assertEqual(summary["total"], 6)
        self.assertEqual(summary["compliant"], 3)
        self.assertEqual(summary["non_compliant"], 1)
        self.assertEqual(summary["unreachable"], 1)
        self.assertEqual(summary["error"], 1)
        self.assertTrue(all("report_id" in agent for agent in summary["agents"]))
        self.assertIsNone(next(agent for agent in summary["agents"] if agent["name"] == "Malformed")["report_id"])
        self.assertIsNone(next(agent for agent in summary["agents"] if agent["slug"] == "legacy")["report_id"])
        self.assertEqual(len(list((self.site_dir / "badges").glob("*.json"))), 6)
        badge = json.loads((self.site_dir / "badges" / "compliant.json").read_text(encoding="utf-8"))
        self.assertEqual(badge, {"schemaVersion": 1, "label": "Compliant", "message": "compliant", "color": "brightgreen"})

    def test_agent_rows_have_stable_fragment_ids(self):
        self.assertIn('<tr id="agent-compliant">', self.page)
        self.assertIn('<tr id="agent-non-compliant">', self.page)


if __name__ == "__main__":
    unittest.main()
