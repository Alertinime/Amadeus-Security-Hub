import sys
import types
import unittest
from pathlib import Path
from unittest.mock import Mock


APP_DIR = Path(__file__).resolve().parents[1] / "app"
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

sys.modules["pywintypes"] = types.SimpleNamespace(
    error=Exception,
    SECURITY_ATTRIBUTES=lambda: types.SimpleNamespace(),
)
sys.modules["win32api"] = types.SimpleNamespace(GetUserName=lambda: "tester")
sys.modules["win32file"] = types.SimpleNamespace(
    GENERIC_READ=1,
    GENERIC_WRITE=2,
    CloseHandle=lambda handle: None,
)
sys.modules["win32pipe"] = types.SimpleNamespace()
sys.modules["win32security"] = types.SimpleNamespace()

from Backend.IPC.LinuxUnixSocketHandler import UnixSocketServer, get_socket_path
from Backend.IPC.WinNamedPipesHandler import NamedPipeServer


class IPCHandlersTest(unittest.TestCase):
    def _assert_ask_dispatch(self, server):
        server.passctrl.getpsswd.return_value = "secret"

        response = server._dispatch({
            "id": "request-1",
            "type": "Ask",
            "domaine": "example.com",
        })

        self.assertEqual(
            response,
            {
                "id": "request-1",
                "ok": True,
                "type": "password_response",
                "value": "secret",
            },
        )
        server.passctrl.getpsswd.assert_called_once_with(server.usb, "example.com")

    def _assert_add_dispatch(self, server):
        server.passctrl.addentry.return_value = True

        response = server._dispatch({
            "id": "request-2",
            "type": "AddEntry",
            "domaine": "example.com",
            "password": "secret",
        })

        self.assertEqual(
            response,
            {
                "id": "request-2",
                "ok": True,
                "type": "password_saved",
                "value": True,
            },
        )
        server.passctrl.addentry.assert_called_once_with(
            server.usb,
            "example.com",
            "secret",
        )

    def test_linux_ipc_dispatches_ask_like_windows_contract(self):
        server = UnixSocketServer(passwordctrl=Mock(), usb="/media/key/USBSecurity")

        self._assert_ask_dispatch(server)

    def test_windows_ipc_dispatches_ask_like_linux_contract(self):
        server = NamedPipeServer(passwordctrl=Mock(), usb="E:\\USBSecurity")

        self._assert_ask_dispatch(server)

    def test_linux_ipc_dispatches_add_entry_like_windows_contract(self):
        server = UnixSocketServer(passwordctrl=Mock(), usb="/media/key/USBSecurity")

        self._assert_add_dispatch(server)

    def test_windows_ipc_dispatches_add_entry_like_linux_contract(self):
        server = NamedPipeServer(passwordctrl=Mock(), usb="E:\\USBSecurity")

        self._assert_add_dispatch(server)

    def test_linux_ipc_rejects_missing_add_entry_fields(self):
        server = UnixSocketServer(passwordctrl=Mock(), usb="/media/key/USBSecurity")

        response = server._dispatch({
            "id": "request-3",
            "type": "AddEntry",
            "domaine": "example.com",
        })

        self.assertEqual(response["ok"], False)
        self.assertEqual(response["type"], "password_saved")
        server.passctrl.addentry.assert_not_called()

    def test_ipc_returns_error_for_unsupported_message_type(self):
        server = UnixSocketServer(passwordctrl=Mock(), usb="/media/key/USBSecurity")

        response = server._dispatch({"id": "request-4", "type": "Unknown"})

        self.assertEqual(response["id"], "request-4")
        self.assertEqual(response["ok"], False)
        self.assertIn("Unsupported message type", response["error"])

    def test_linux_socket_path_uses_configured_environment_value(self):
        import os

        previous = os.environ.get("AMADEUS_SECURITY_HUB_SOCKET")
        os.environ["AMADEUS_SECURITY_HUB_SOCKET"] = "/tmp/custom-ash.sock"
        try:
            self.assertEqual(get_socket_path(), "/tmp/custom-ash.sock")
        finally:
            if previous is None:
                os.environ.pop("AMADEUS_SECURITY_HUB_SOCKET", None)
            else:
                os.environ["AMADEUS_SECURITY_HUB_SOCKET"] = previous


if __name__ == "__main__":
    unittest.main()
