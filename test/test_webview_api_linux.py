import base64
import io
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import Mock, patch


APP_DIR = Path(__file__).resolve().parents[1] / "app"
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from Backend.WebviewAPILinux import Api


class WebviewAPILinuxTest(unittest.TestCase):
    def test_login_stores_secret_when_usb_login_succeeds(self):
        api = Api()
        secret = base64.b64encode(b"p" * 32).decode("ascii")
        api.usb = "/tmp/USBSecurity"
        api.key_listener = Mock()
        api.key_listener.login_usb.return_value = secret

        with patch("Backend.WebviewAPILinux.start_unix_socket_server") as start_server:
            with redirect_stdout(io.StringIO()):
                result = api.login("password")

        self.assertTrue(result)
        self.assertEqual(api.pswctrl.secret, secret)
        api.key_listener.login_usb.assert_called_once_with("/tmp/USBSecurity", "password")
        start_server.assert_called_once_with(api.pswctrl, "/tmp/USBSecurity")

    def test_login_does_not_start_ipc_when_usb_login_fails(self):
        api = Api()
        api.usb = "/tmp/USBSecurity"
        api.key_listener = Mock()
        api.key_listener.login_usb.return_value = False

        with patch("Backend.WebviewAPILinux.start_unix_socket_server") as start_server:
            with redirect_stdout(io.StringIO()):
                result = api.login("password")

        self.assertFalse(result)
        start_server.assert_not_called()

    def test_login_returns_false_when_ipc_start_raises(self):
        api = Api()
        api.usb = "/tmp/USBSecurity"
        secret = base64.b64encode(b"p" * 32).decode("ascii")
        api.key_listener = Mock()
        api.key_listener.login_usb.return_value = secret

        with patch(
            "Backend.WebviewAPILinux.start_unix_socket_server",
            side_effect=RuntimeError("ipc failed"),
        ):
            with redirect_stdout(io.StringIO()):
                result = api.login("password")

        self.assertFalse(result)

    def test_login_returns_false_when_listener_raises(self):
        api = Api()
        api.usb = "/tmp/USBSecurity"
        api.key_listener = Mock()
        api.key_listener.login_usb.side_effect = RuntimeError("boom")

        with patch("Backend.WebviewAPILinux.start_unix_socket_server"):
            with redirect_stdout(io.StringIO()):
                result = api.login("password")

        self.assertFalse(result)

    def test_reload_usb_check_returns_nokey_when_no_usb_devices_are_found(self):
        api = Api()
        api.key_listener = Mock()
        api.key_listener.list_usb.return_value = []
        api.key_listener.check_for_security_key.return_value = False

        self.assertEqual(api.reload_usb_check(), "Nokey.html")
        self.assertIsNone(api.usb)

    def test_reload_usb_check_returns_create_key_when_usb_has_no_security_key(self):
        api = Api()
        usb_devices = [{"product": "USB Drive"}]
        api.key_listener = Mock()
        api.key_listener.list_usb.return_value = usb_devices
        api.key_listener.check_for_security_key.return_value = False

        self.assertEqual(api.reload_usb_check(), "CreateKey.html")
        self.assertIsNone(api.usb)

    def test_reload_usb_check_returns_login_when_security_key_exists(self):
        api = Api()
        usb_devices = [{"product": "USB Drive"}]
        security_usb = {"security_mount": "/media/key"}
        api.key_listener = Mock()
        api.key_listener.list_usb.return_value = usb_devices
        api.key_listener.check_for_security_key.return_value = security_usb
        api.key_listener.get_security_dir.return_value = "/media/key/USBSecurity"

        self.assertEqual(api.reload_usb_check(), "Login.html")
        self.assertEqual(api.usb, "/media/key/USBSecurity")

    def test_update_password_data_returns_refreshed_site_list(self):
        api = Api()
        api.usb = "/tmp/USBSecurity"
        api.pswctrl = Mock()
        api.pswctrl.update_file_with_new_data.return_value = True
        api.get_data_list_from_pswctrl = Mock(return_value=[{"url": "https://example.com"}])
        data = {"sites": [{"url": "https://example.com", "password": "secret"}]}

        self.assertEqual(api.update_password_data(data), [{"url": "https://example.com"}])
        api.pswctrl.update_file_with_new_data.assert_called_once_with("/tmp/USBSecurity", data)
        api.get_data_list_from_pswctrl.assert_called_once_with("/tmp/USBSecurity")

    def test_get_data_list_from_pswctrl_returns_false_when_controller_fails(self):
        api = Api()
        api.pswctrl = Mock()
        api.pswctrl.get_file_data.return_value = False

        with redirect_stdout(io.StringIO()):
            result = api.get_data_list_from_pswctrl("/tmp/USBSecurity")

        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
