import json
import os
import socket


SOCKET_ENV = "AMADEUS_SECURITY_HUB_SOCKET"
SOCKET_NAME = "amadeus-security-hub.sock"
BUFFER_SIZE = 64 * 1024


def get_socket_path():
    configured_path = os.environ.get(SOCKET_ENV)
    if configured_path:
        return configured_path

    runtime_dir = os.environ.get("XDG_RUNTIME_DIR")
    if runtime_dir and os.path.isdir(runtime_dir):
        return os.path.join(runtime_dir, SOCKET_NAME)

    uid = os.getuid() if hasattr(os, "getuid") else "user"
    return os.path.join("/tmp", f"amadeus-security-hub-{uid}.sock")


class LinuxUnixSocket:
    def __init__(self, socket_path=None, timeout=3.0):
        self.socket_path = socket_path or get_socket_path()
        self.timeout = timeout

    def request(self, message):
        client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        client.settimeout(self.timeout)
        try:
            client.connect(self.socket_path)
            self._write_message(client, message)
            client.shutdown(socket.SHUT_WR)
            return self._read_message(client)
        finally:
            client.close()

    def _write_message(self, client, message):
        encoded = json.dumps(message).encode("utf-8")
        client.sendall(encoded)

    def _read_message(self, client):
        chunks = []

        while True:
            data = client.recv(BUFFER_SIZE)
            if not data:
                break
            chunks.append(data)

        return json.loads(b"".join(chunks).decode("utf-8"))


def pipe_request(message):
    try:
        return LinuxUnixSocket().request(message)
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "id": message.get("id") if isinstance(message, dict) else None,
            "ok": False,
            "error": f"ipc_unavailable: {exc}",
        }
