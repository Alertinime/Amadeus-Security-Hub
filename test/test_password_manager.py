import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch


APP_DIR = Path(__file__).resolve().parents[1] / "app"
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from Backend.Cryptography.PasswordManager import PasswordManager


class PasswordManagerTest(unittest.TestCase):
    def test_create_salt_returns_16_random_bytes(self):
        manager = PasswordManager()
        expected_salt = b"x" * 16

        with patch("Backend.Cryptography.PasswordManager.os.urandom", return_value=expected_salt) as urandom:
            self.assertEqual(manager.create_salt(), expected_salt)

        urandom.assert_called_once_with(16)

    def test_kdf_uses_argon2id_with_project_parameters(self):
        manager = PasswordManager()
        salt = b"1" * 16
        fake_kdf = Mock()
        fake_kdf.derive.return_value = b"derived-key"

        with patch("Backend.Cryptography.PasswordManager.Argon2id", return_value=fake_kdf) as argon2id:
            result = manager.kdf("secret", salt)

        self.assertEqual(result, b"derived-key")
        argon2id.assert_called_once_with(
            length=32,
            salt=salt,
            iterations=1,
            memory_cost=2_097_152,
            lanes=8,
        )
        fake_kdf.derive.assert_called_once_with(b"secret")

    def test_hkdf_is_deterministic_for_same_inputs(self):
        manager = PasswordManager()
        key_material = b"k" * 32

        first = manager.HKDF(key_material, b"salt", "Master_Key", 32)
        second = manager.HKDF(key_material, b"salt", "Master_Key", 32)

        self.assertEqual(first, second)
        self.assertEqual(len(first), 32)

    def test_hkdf_accepts_string_salt(self):
        manager = PasswordManager()

        result = manager.HKDF(b"k" * 32, "salt", "Master_Key", 16)

        self.assertIsInstance(result, bytes)
        self.assertEqual(len(result), 16)


if __name__ == "__main__":
    unittest.main()
