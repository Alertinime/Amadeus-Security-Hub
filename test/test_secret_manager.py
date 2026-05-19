import sys
import unittest
from pathlib import Path
from unittest.mock import patch


APP_DIR = Path(__file__).resolve().parents[1] / "app"
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from Backend.Cryptography.SecretManager import SecretManager


class SecretManagerTest(unittest.TestCase):
    def test_generate_random_key_returns_32_random_bytes(self):
        manager = SecretManager()
        expected_key = b"k" * 32

        with patch("Backend.Cryptography.SecretManager.os.urandom", return_value=expected_key) as urandom:
            self.assertEqual(manager.generate_random_key(), expected_key)

        urandom.assert_called_once_with(32)

    def test_generate_salt_returns_32_random_bytes(self):
        manager = SecretManager()
        expected_salt = b"s" * 32

        with patch("Backend.Cryptography.SecretManager.os.urandom", return_value=expected_salt) as urandom:
            self.assertEqual(manager.generate_salt(), expected_salt)

        urandom.assert_called_once_with(32)

    def test_generate_aad_returns_16_random_bytes(self):
        manager = SecretManager()
        expected_aad = b"a" * 16

        with patch("Backend.Cryptography.SecretManager.os.urandom", return_value=expected_aad) as urandom:
            self.assertEqual(manager.generate_aad(), expected_aad)

        urandom.assert_called_once_with(16)

    def test_store_secret_keeps_secret_by_key(self):
        manager = SecretManager()

        manager.store_secret("PasswordManagerKey", b"secret")

        self.assertEqual(manager.secrets_dict["PasswordManagerKey"], b"secret")


if __name__ == "__main__":
    unittest.main()
