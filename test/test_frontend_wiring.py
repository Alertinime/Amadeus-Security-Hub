import shutil
import subprocess
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
HTML_DIR = REPO_ROOT / "app" / "Frontend" / "Html"
JS_DIR = HTML_DIR / "JS"


class FrontendWiringTest(unittest.TestCase):
    def test_nokey_referenced_script_exists_and_buttons_are_addressable(self):
        nokey_html = (HTML_DIR / "Nokey.html").read_text(encoding="utf-8")

        self.assertIn('src="JS/nokey.js"', nokey_html)
        self.assertTrue((JS_DIR / "nokey.js").is_file())
        self.assertIn("data-retry-detection", nokey_html)
        self.assertIn("data-quit-app", nokey_html)

    def test_nokey_script_retries_detection_and_navigates_to_backend_page(self):
        nokey_js = (JS_DIR / "nokey.js").read_text(encoding="utf-8")

        self.assertIn("reload_usb_check", nokey_js)
        self.assertIn("nextPage", nokey_js)
        self.assertIn("goToPage(nextPage)", nokey_js)
        self.assertIn("window.location.href = nextPage", nokey_js)

    def test_nokey_quit_button_is_wired(self):
        nokey_js = (JS_DIR / "nokey.js").read_text(encoding="utf-8")

        self.assertIn("data-quit-app", nokey_js)
        self.assertIn("window.close()", nokey_js)

    def test_create_key_back_button_uses_reload_result_for_navigation(self):
        create_key_js = (JS_DIR / "create_key.js").read_text(encoding="utf-8")

        self.assertIn("let nextPage", create_key_js)
        self.assertIn("nextPage = await callApi('reload_usb_check')", create_key_js)
        self.assertIn("nextPage = await api.reload_usb_check()", create_key_js)
        self.assertIn("goToPage(nextPage)", create_key_js)
        self.assertIn("window.location.href = nextPage", create_key_js)

    def test_dashboard_refresh_button_reloads_sites(self):
        dashboard_html = (HTML_DIR / "Dashboard.html").read_text(encoding="utf-8")
        dashboard_js = (JS_DIR / "dashboard.js").read_text(encoding="utf-8")

        self.assertIn('id="refresh-dashboard-button"', dashboard_html)
        self.assertIn("refreshDashboardButton", dashboard_js)
        self.assertIn("await loadSites()", dashboard_js)

    @unittest.skipIf(shutil.which("node") is None, "node is not installed")
    def test_frontend_scripts_are_valid_javascript(self):
        for script in ("create_key.js", "nokey.js", "dashboard.js"):
            with self.subTest(script=script):
                subprocess.run(
                    ["node", "--check", str(JS_DIR / script)],
                    check=True,
                    capture_output=True,
                    text=True,
                )


if __name__ == "__main__":
    unittest.main()
