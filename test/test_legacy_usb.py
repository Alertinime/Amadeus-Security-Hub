import base64
import importlib.util
import io
import json
import os
import sys
import tempfile
import unittest
import uuid
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


APP_DIR = Path(__file__).resolve().parents[1] / "app"
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

USB_MODULE_PATH = APP_DIR / "Backend" / "Key" / "key-read&write" / "USB.py"
USB = None
USB_IMPORT_ERROR = None

try:
    original_tkinter = sys.modules.get("tkinter")
    original_argon2 = sys.modules.get("argon2")
    original_argon2_low_level = sys.modules.get("argon2.low_level")
    sys.modules["tkinter"] = SimpleNamespace(_default_root=None)
    sys.modules["argon2"] = SimpleNamespace()
    sys.modules["argon2.low_level"] = SimpleNamespace(
        hash_secret_raw=lambda **kwargs: b"k" * 32,
        Type=SimpleNamespace(ID="ID"),
    )
    spec = importlib.util.spec_from_file_location("legacy_usb_module", USB_MODULE_PATH)
    legacy_usb_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(legacy_usb_module)
    USB = legacy_usb_module.USB
except Exception as exc:
    USB_IMPORT_ERROR = exc
finally:
    if "original_tkinter" in locals():
        if original_tkinter is None:
            sys.modules.pop("tkinter", None)
        else:
            sys.modules["tkinter"] = original_tkinter
        if original_argon2 is None:
            sys.modules.pop("argon2", None)
        else:
            sys.modules["argon2"] = original_argon2
        if original_argon2_low_level is None:
            sys.modules.pop("argon2.low_level", None)
        else:
            sys.modules["argon2.low_level"] = original_argon2_low_level


@unittest.skipIf(USB_IMPORT_ERROR is not None, f"legacy USB module import failed: {USB_IMPORT_ERROR}")
class LegacyUSBTest(unittest.TestCase):
    def test_prepare_data_returns_decryptable_package(self):
        usb = USB(SimpleNamespace(Caption="/tmp"))
        encryption_key = b"k" * 32

        package = usb.prepare_data(encryption_key)
        plaintext = AESGCM(encryption_key).decrypt(
            base64.b64decode(package["iv"]),
            base64.b64decode(package["data"]),
            None,
        )
        payload = json.loads(plaintext.decode("utf-8"))

        uuid.UUID(payload["UUID"])
        self.assertEqual(len(base64.b64decode(payload["key"])), 32)

    def test_get_data_decrypts_existing_usb_key_file(self):
        encryption_key = b"k" * 32

        with tempfile.TemporaryDirectory() as mount:
            usb = USB(SimpleNamespace(Caption=mount))
            package = usb.prepare_data(encryption_key)
            security_dir = Path(mount) / "USBSecurity"
            os.makedirs(security_dir)
            with open(security_dir / "USBKey.rin", "w", encoding="utf-8") as file:
                json.dump(package, file)

            result = usb.get_data(encryption_key)

        self.assertIn("UUID", result)
        self.assertEqual(len(base64.b64decode(result["key"])), 32)

    def test_get_data_returns_false_when_key_file_is_missing(self):
        with tempfile.TemporaryDirectory() as mount:
            usb = USB(SimpleNamespace(Caption=mount))

            self.assertFalse(usb.get_data(b"k" * 32))

    def test_is_usb_returns_false_for_missing_path(self):
        usb = USB(SimpleNamespace(caption="/path/that/does/not/exist"))

        with redirect_stdout(io.StringIO()):
            result = usb.is_usb()

        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
