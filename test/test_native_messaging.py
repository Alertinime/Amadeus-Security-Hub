import importlib
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch


NATIVE_DIR = Path(__file__).resolve().parents[1] / "extension" / "NativesMessages"
if str(NATIVE_DIR) not in sys.path:
    sys.path.insert(0, str(NATIVE_DIR))


class NativeMessagingTest(unittest.TestCase):
    def test_pipeline_uses_linux_ipc_on_posix(self):
        pipeline = importlib.import_module("NativesPipeline")

        self.assertEqual(pipeline.pipe_request.__module__, "IPC.LinuxUnixSocket")

    def test_pipeline_reports_unsupported_os_without_crashing(self):
        pipeline = importlib.import_module("NativesPipeline")

        with patch.object(pipeline.os, "name", "other"):
            request = pipeline._load_pipe_request()
            self.assertEqual(
                request({"id": "unsupported"}),
                {
                    "id": "unsupported",
                    "ok": False,
                    "error": "unsupported_os: other",
                },
            )

    def test_linux_native_client_returns_ipc_error_when_socket_fails(self):
        linux_ipc = importlib.import_module("IPC.LinuxUnixSocket")

        with patch.object(linux_ipc.LinuxUnixSocket, "request", side_effect=OSError("boom")):
            response = linux_ipc.pipe_request({"id": "request-1"})

        self.assertEqual(response["id"], "request-1")
        self.assertEqual(response["ok"], False)
        self.assertIn("ipc_unavailable", response["error"])

    def test_linux_native_client_writes_json_and_reads_json_response(self):
        linux_ipc = importlib.import_module("IPC.LinuxUnixSocket")
        fake_socket = Mock()
        fake_socket.recv.side_effect = [
            json.dumps({"id": "request-2", "ok": True}).encode("utf-8"),
            b"",
        ]

        with patch.object(linux_ipc.socket, "socket", return_value=fake_socket):
            response = linux_ipc.LinuxUnixSocket("/tmp/ash.sock").request({
                "id": "request-2",
                "type": "Ask",
            })

        fake_socket.settimeout.assert_called_once_with(3.0)
        fake_socket.connect.assert_called_once_with("/tmp/ash.sock")
        fake_socket.sendall.assert_called_once_with(
            json.dumps({"id": "request-2", "type": "Ask"}).encode("utf-8")
        )
        fake_socket.shutdown.assert_called_once_with(linux_ipc.socket.SHUT_WR)
        fake_socket.close.assert_called_once()
        self.assertEqual(response, {"id": "request-2", "ok": True})


if __name__ == "__main__":
    unittest.main()
