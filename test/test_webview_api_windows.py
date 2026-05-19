import base64
import io
import sys
import types
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import Mock, patch


APP_DIR = Path(__file__).resolve().parents[1] / "app"
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

sys.modules["wmi"] = types.SimpleNamespace(WMI=lambda: object())

from Backend.WebviewAPIWindows import Api


class WebviewAPIWindowsTest(unittest.TestCase):
    def test_login_stores_secret_when_usb_login_succeeds(self):
        api = Api()
        api.usb = "E:\\USBSecurity"
        secret = base64.b64encode(b"p" * 32).decode("ascii")
        fake_key_listing = Mock()
        fake_key_listing.login_usb.return_value = secret

        with patch("Backend.WebviewAPIWindows.key_listing_win", return_value=fake_key_listing):
            with redirect_stdout(io.StringIO()):
                result = api.login("password")

        self.assertTrue(result)
        self.assertEqual(api.pswctrl.secret, secret)
        fake_key_listing.login_usb.assert_called_once_with("E:\\USBSecurity", "password")

    def test_login_returns_false_when_key_listing_raises(self):
        api = Api()
        fake_key_listing = Mock()
        fake_key_listing.login_usb.side_effect = RuntimeError("boom")

        with patch("Backend.WebviewAPIWindows.key_listing_win", return_value=fake_key_listing):
            with redirect_stdout(io.StringIO()):
                result = api.login("password")

        self.assertFalse(result)

    def test_reload_usb_check_returns_nokey_when_no_usb_devices_are_found(self):
        api = Api()
        fake_key_listing = Mock()
        fake_key_listing.check_for_key.return_value = False

        with patch("Backend.WebviewAPIWindows.key_listing_win", return_value=fake_key_listing):
            self.assertEqual(api.reload_usb_check(), "Nokey.html")

        self.assertIsNone(api.usb)

    def test_reload_usb_check_returns_create_key_when_usb_has_no_security_key(self):
        api = Api()
        usb_devices = [Mock(Caption="E:")]
        fake_key_listing = Mock()
        fake_key_listing.check_for_key.return_value = usb_devices
        fake_key_listing.check_for_security_key.return_value = False

        with patch("Backend.WebviewAPIWindows.key_listing_win", return_value=fake_key_listing):
            self.assertEqual(api.reload_usb_check(), "CreateKey.html")

        self.assertIsNone(api.usb)

    def test_reload_usb_check_returns_login_when_security_key_exists(self):
        api = Api()
        security_usb = Mock(Caption="E:")
        fake_key_listing = Mock()
        fake_key_listing.check_for_key.return_value = [security_usb]
        fake_key_listing.check_for_security_key.return_value = security_usb
        fake_key_listing.get_security_dir.return_value = "E:\\USBSecurity"

        with patch("Backend.WebviewAPIWindows.key_listing_win", return_value=fake_key_listing):
            self.assertEqual(api.reload_usb_check(), "Login.html")

        self.assertEqual(api.usb, "E:\\USBSecurity")

    def test_update_password_data_returns_refreshed_site_list(self):
        api = Api()
        api.usb = "E:\\USBSecurity"
        api.pswctrl = Mock()
        api.pswctrl.update_file_with_new_data.return_value = True
        api.get_data_list_from_pswctrl = Mock(return_value=[{"url": "https://example.com"}])
        data = {"sites": [{"url": "https://example.com", "password": "secret"}]}

        self.assertEqual(api.update_password_data(data), [{"url": "https://example.com"}])
        api.pswctrl.update_file_with_new_data.assert_called_once_with("E:\\USBSecurity", data)
        api.get_data_list_from_pswctrl.assert_called_once_with("E:\\USBSecurity")


if __name__ == "__main__":
    unittest.main()
