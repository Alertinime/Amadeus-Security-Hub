import base64
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path


APP_DIR = Path(__file__).resolve().parents[1] / "app"
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from Backend.Controller.AMHSPswdCtrl import Pswctrl


class PswctrlTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = self.tmp.name
        self.ctrl = Pswctrl()
        self.secret_key = b"s" * 32
        self.ctrl.set_secret(base64.b64encode(self.secret_key).decode("ascii"))
        self.header = {
            "version": 1,
            "type": "security-hub-password-manager",
            "aad": base64.b64encode(b"associated-data").decode("ascii"),
        }

    def tearDown(self):
        self.tmp.cleanup()

    def test_encrypt_file_then_decrypt_file_round_trip(self):
        data = {"sites": [{"url": "https://example.com", "password": "secret"}]}

        self.assertTrue(self.ctrl.encrypt_file(self.path, self.header, data))
        header, decrypted = self.ctrl.decrypt_file(self.path)

        self.assertEqual(decrypted, data)
        self.assertEqual(header["aad"], self.header["aad"])
        self.assertIn("nonce", header)

    def test_update_file_with_new_data_appends_sites(self):
        existing_data = {"sites": [{"url": "https://old.example", "password": "old"}]}
        new_data = {"sites": [{"url": "https://new.example", "password": "new"}]}
        self.assertTrue(self.ctrl.encrypt_file(self.path, self.header, existing_data))

        self.assertTrue(self.ctrl.update_file_with_new_data(self.path, new_data))

        self.assertEqual(
            self.ctrl.get_file_data(self.path),
            {"sites": existing_data["sites"] + new_data["sites"]},
        )

    def test_read_in_file_returns_false_for_missing_header_or_payload(self):
        file_path = Path(self.path) / "PasswordManager.Archer"
        with open(file_path, "w", encoding="utf-8") as file:
            json.dump({"header": {}, "payload": {}}, file)

        self.assertFalse(self.ctrl.read_in_file(self.path))

    def test_get_header_aad_returns_none_for_invalid_base64(self):
        with redirect_stdout(io.StringIO()):
            result = self.ctrl.get_header_aad({"aad": "not valid base64 !!!"}, self.path)

        self.assertIsNone(result)

    def test_concatenate_file_and_new_data_rejects_non_list_sites(self):
        self.assertTrue(self.ctrl.encrypt_file(self.path, self.header, {"sites": {}}))

        with redirect_stdout(io.StringIO()):
            result = self.ctrl.concatenate_file_and_new_data(
                self.path,
                {"sites": [{"url": "https://example.com", "password": "secret"}]},
            )

        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
