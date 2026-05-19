import base64
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import Mock, patch

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


APP_DIR = Path(__file__).resolve().parents[1] / "app"
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from Backend.Key.KeyListingLinux import key_listening_linux


class KeyListingLinuxTest(unittest.TestCase):
    def setUp(self):
        self.listener = key_listening_linux()

    def test_decode_mount_path_handles_proc_mount_escapes(self):
        self.assertEqual(
            self.listener._decode_mount_path("/media/My\\040USB\\011Tab\\134Drive"),
            "/media/My USB\tTab\\Drive",
        )

    def test_get_security_dir_prefers_explicit_security_key_path(self):
        usb = {
            "security_key_path": "/media/key/USBSecurity/USBKey.rin",
            "security_mount": "/ignored",
            "mounts": ["/also-ignored"],
        }

        self.assertEqual(
            self.listener.get_security_dir(usb),
            "/media/key/USBSecurity",
        )

    def test_get_security_dir_falls_back_to_mounts(self):
        self.assertEqual(
            self.listener.get_security_dir({"mounts": ["/media/key"]}),
            "/media/key/USBSecurity",
        )

    def test_get_usb_name_and_id_use_available_metadata(self):
        usb = {
            "product": "USB Drive",
            "manufacturer": "Vendor",
            "serial": "SERIAL123",
            "sysname": "1-1",
        }

        self.assertEqual(self.listener.get_usb_name(usb), "USB Drive")
        self.assertEqual(self.listener.get_usb_id(usb), "SERIAL123")

    def test_list_usb_for_frontend_maps_usb_metadata(self):
        self.listener.list_usb = Mock(
            return_value=[
                {"serial": "SERIAL123", "product": "USB Drive"},
                {"idVendor": "abcd", "idProduct": "1234", "sysname": "1-2"},
            ]
        )

        self.assertEqual(
            self.listener.list_usb_for_frontend(),
            [
                {"id": "SERIAL123", "name": "USB Drive"},
                {"id": "1-2", "name": "1-2"},
            ],
        )

    def test_normalize_password_entries_accepts_aliases_and_pairs(self):
        self.assertEqual(
            self.listener._normalize_password_entries(
                [
                    {"site": "https://example.com", "secret": "pw1"},
                    ("https://example.org", "pw2"),
                ]
            ),
            [
                {"url": "https://example.com", "password": "pw1"},
                {"url": "https://example.org", "password": "pw2"},
            ],
        )

    def test_normalize_password_entries_rejects_invalid_entries(self):
        self.assertIsNone(self.listener._normalize_password_entries("not a list"))
        self.assertIsNone(self.listener._normalize_password_entries([{"url": 42, "password": "pw"}]))

    def test_make_password_manager_file_writes_decryptable_package(self):
        password_manager_key = b"p" * 32
        passwords = [{"website": "https://example.com", "pass": "pw"}]

        with tempfile.TemporaryDirectory() as mount:
            usb = {"security_mount": mount, "product": "Test USB"}

            with redirect_stdout(io.StringIO()):
                result = self.listener.make_passwordManager_file(usb, password_manager_key, passwords)

            self.assertTrue(result)

            package_path = Path(mount) / "USBSecurity" / "PasswordManager.Archer"
            with open(package_path, "r", encoding="utf-8") as file:
                package = json.load(file)

        header = package["header"]
        plaintext = AESGCM(password_manager_key).decrypt(
            base64.b64decode(header["nonce"]),
            base64.b64decode(package["payload"]),
            base64.b64decode(header["aad"]),
        )

        self.assertEqual(
            json.loads(plaintext.decode("utf-8")),
            {"sites": [{"url": "https://example.com", "password": "pw"}]},
        )

    def test_make_password_manager_file_rejects_invalid_key_length(self):
        with tempfile.TemporaryDirectory() as mount:
            usb = {"security_mount": mount, "product": "Test USB"}

            with redirect_stdout(io.StringIO()):
                result = self.listener.make_passwordManager_file(usb, b"short")

            self.assertFalse(result)

    def test_login_usb_returns_password_manager_key_from_master_file(self):
        master_key = b"m" * 32
        password_manager_key = b"p" * 32
        password_manager_key_b64 = base64.b64encode(password_manager_key).decode("ascii")
        aad = b"a" * 16
        nonce = b"n" * 12
        ciphertext = AESGCM(master_key).encrypt(
            nonce,
            json.dumps({"PasswordManagerKey": password_manager_key_b64}).encode("utf-8"),
            aad,
        )

        with tempfile.TemporaryDirectory() as security_dir:
            package_path = Path(security_dir) / "USBKey.rin"
            with open(package_path, "w", encoding="utf-8") as file:
                json.dump(
                    {
                        "header": {
                            "password_salt": base64.b64encode(b"salt").decode("ascii"),
                            "hkdf_salt": base64.b64encode(b"hkdf-salt").decode("ascii"),
                            "nonce": base64.b64encode(nonce).decode("ascii"),
                            "aad": base64.b64encode(aad).decode("ascii"),
                        },
                        "payload": base64.b64encode(ciphertext).decode("ascii"),
                    },
                    file,
                )

            fake_password_manager = Mock()
            fake_password_manager.kdf.return_value = b"kdf-key"
            fake_password_manager.HKDF.return_value = master_key

            with patch(
                "Backend.Key.KeyListingLinux.PasswordManager",
                return_value=fake_password_manager,
            ):
                with redirect_stdout(io.StringIO()):
                    result = self.listener.login_usb(
                        {"security_key_path": str(package_path), "product": "USB Drive"},
                        "password",
                    )

        self.assertEqual(result, password_manager_key_b64)
        fake_password_manager.kdf.assert_called_once_with("password", b"salt")
        fake_password_manager.HKDF.assert_called_once_with(b"kdf-key", b"hkdf-salt", "Master_Key", 32)


if __name__ == "__main__":
    unittest.main()
