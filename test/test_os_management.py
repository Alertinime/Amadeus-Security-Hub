import sys
import unittest
from pathlib import Path
from unittest.mock import patch


APP_DIR = Path(__file__).resolve().parents[1] / "app"
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from Backend.OSManagement import OSspliter


class OSspliterTest(unittest.TestCase):
    def test_get_current_os_returns_os_name(self):
        with patch("Backend.OSManagement.os.name", "posix"):
            self.assertEqual(OSspliter().get_current_os(), "posix")


if __name__ == "__main__":
    unittest.main()
