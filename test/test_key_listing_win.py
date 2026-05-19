import sys
import types
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock


APP_DIR = Path(__file__).resolve().parents[1] / "app"
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

sys.modules["wmi"] = types.SimpleNamespace(WMI=lambda: object())

from Backend.Key.KeyListingWin import key_listing_win


class KeyListingWinTest(unittest.TestCase):
    def setUp(self):
        self.listener = key_listing_win()

    def test_get_usb_root_normalizes_drive_letter(self):
        self.assertEqual(self.listener._get_usb_root(SimpleNamespace(Caption="E:")), "E:\\")

    def test_get_usb_root_strips_trailing_separators(self):
        self.assertEqual(self.listener._get_usb_root(SimpleNamespace(Caption="E:\\")), "E:\\")

    def test_list_usb_for_frontend_returns_empty_when_no_usb(self):
        self.listener.check_for_key = Mock(return_value=False)

        self.assertEqual(self.listener.list_usb_for_frontend(), [])

    def test_list_usb_for_frontend_maps_caption_and_name(self):
        usb = SimpleNamespace(Caption="E:", DeviceID="E:", DriveType=2)
        self.listener.check_for_key = Mock(return_value=[usb])
        self.listener.get_usb_name = Mock(return_value="USB Drive")

        self.assertEqual(
            self.listener.list_usb_for_frontend(),
            [{"id": "E:", "name": "USB Drive"}],
        )

    def test_normalize_password_entries_accepts_aliases_and_pairs(self):
        self.assertEqual(
            self.listener._normalize_password_entries(
                [
                    {"url": "https://example.com", "password": "pw1"},
                    ("https://example.org", "pw2"),
                ]
            ),
            [
                {"url": "https://example.com", "password": "pw1"},
                {"url": "https://example.org", "password": "pw2"},
            ],
        )

    def test_normalize_password_entries_rejects_invalid_entries(self):
        self.assertIsNone(self.listener._normalize_password_entries({"url": "https://example.com"}))
        self.assertIsNone(self.listener._normalize_password_entries([("only-one-value",)]))


if __name__ == "__main__":
    unittest.main()
