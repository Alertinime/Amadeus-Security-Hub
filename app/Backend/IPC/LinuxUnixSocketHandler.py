import json
import os
import socket
import threading


SOCKET_ENV = "AMADEUS_SECURITY_HUB_SOCKET"
SOCKET_NAME = "amadeus-security-hub.sock"
BUFFER_SIZE = 64 * 1024

_server = None
_server_lock = threading.Lock()


def get_socket_path():
    configured_path = os.environ.get(SOCKET_ENV)
    if configured_path:
        return configured_path

    runtime_dir = os.environ.get("XDG_RUNTIME_DIR")
    if runtime_dir and os.path.isdir(runtime_dir):
        return os.path.join(runtime_dir, SOCKET_NAME)

    uid = os.getuid() if hasattr(os, "getuid") else "user"
    return os.path.join("/tmp", f"amadeus-security-hub-{uid}.sock")


class UnixSocketServer:
    def __init__(self, socket_path=None, passwordctrl=None, usb=None):
        self.socket_path = socket_path or get_socket_path()
        self._stop_event = threading.Event()
        self._thread = None
        self._server_socket = None
        self._current_client = None
        self.passctrl = passwordctrl
        self.usb = usb

    def start(self):
        if self.is_running():
            return False

        if not self._prepare_socket_path():
            return False

        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._serve_forever,
            name="AmadeusUnixSocketServer",
            daemon=True,
        )
        self._thread.start()
        return True

    def stop(self):
        self._stop_event.set()
        self._close_current_client()
        self._close_server_socket()

    def is_running(self):
        return self._thread is not None and self._thread.is_alive()

    def _prepare_socket_path(self):
        socket_dir = os.path.dirname(self.socket_path)
        if socket_dir:
            try:
                os.makedirs(socket_dir, exist_ok=True)
            except OSError as exc:
                print("Unable to create IPC socket directory:", exc)
                return False

        if not os.path.exists(self.socket_path):
            return True

        probe = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            probe.connect(self.socket_path)
        except OSError:
            try:
                os.unlink(self.socket_path)
                return True
            except OSError as exc:
                print("Unable to remove stale IPC socket:", exc)
                return False
        finally:
            probe.close()

        print("IPC socket is already in use:", self.socket_path)
        return False

    def _serve_forever(self):
        server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self._server_socket = server

        try:
            server.bind(self.socket_path)
            os.chmod(self.socket_path, 0o600)
            server.listen(1)

            while not self._stop_event.is_set():
                try:
                    client, _ = server.accept()
                except OSError as exc:
                    if not self._stop_event.is_set():
                        print("Unix socket server error:", exc)
                    break

                self._current_client = client
                try:
                    self._handle_client(client)
                finally:
                    self._close_client(client)
                    self._current_client = None
        except OSError as exc:
            if not self._stop_event.is_set():
                print("Unix socket server error:", exc)
        finally:
            self._close_server_socket()
            self._remove_socket_path()

    def _handle_client(self, client):
        payload = self._read_message(client)
        if payload is None:
            return

        response = self._dispatch(payload)
        self._write_message(client, response)

    def _read_message(self, client):
        chunks = []

        while True:
            data = client.recv(BUFFER_SIZE)
            if not data:
                break
            chunks.append(data)

        if not chunks:
            return None

        try:
            return json.loads(b"".join(chunks).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            return {
                "__ipc_error": f"Invalid JSON message: {exc}",
            }

    def _write_message(self, client, response):
        client.sendall(json.dumps(response).encode("utf-8"))

    def _dispatch(self, payload):
        request_id = payload.get("id") if isinstance(payload, dict) else None

        if not isinstance(payload, dict):
            return _error_response(request_id, "Message must be a JSON object")
        if "__ipc_error" in payload:
            return _error_response(request_id, payload["__ipc_error"])

        message_type = payload.get("type")
        if message_type == "Ask":
            domaine = payload.get("domaine") or payload.get("cible")
            password = self.getPasswordByDomaine(domaine)

            return {
                "id": request_id,
                "ok": True,
                "type": "password_response",
                "value": password,
            }

        if message_type in ("AddEntry", "Modify"):
            domaine = payload.get("domaine") or payload.get("cible")
            password = payload.get("password")
            result = self.addPasswordEntry(domaine, password)

            return {
                "id": request_id,
                "ok": bool(result),
                "type": "password_saved",
                "value": bool(result),
            }

        return _error_response(request_id, f"Unsupported message type: {message_type}")

    def getPasswordByDomaine(self, domaine):
        if self.passctrl is None or self.usb is None:
            return None

        try:
            return self.passctrl.getpsswd(self.usb, domaine)
        except Exception as exc:
            print(f"Error retrieving password for domaine '{domaine}': {exc}")
            return None

    def addPasswordEntry(self, domaine, password):
        if self.passctrl is None or self.usb is None:
            return False
        if not domaine or not password:
            return False

        try:
            return self.passctrl.addentry(self.usb, domaine, password)
        except Exception as exc:
            print(f"Error saving password for domaine '{domaine}': {exc}")
            return False

    def _close_client(self, client):
        try:
            client.close()
        except OSError:
            pass

    def _close_current_client(self):
        if self._current_client is not None:
            self._close_client(self._current_client)

    def _close_server_socket(self):
        if self._server_socket is not None:
            try:
                self._server_socket.close()
            except OSError:
                pass
            self._server_socket = None

    def _remove_socket_path(self):
        try:
            if os.path.exists(self.socket_path):
                os.unlink(self.socket_path)
        except OSError:
            pass


def start_unix_socket_server(pswctrl, usb):
    global _server
    with _server_lock:
        if _server is None:
            _server = UnixSocketServer(passwordctrl=pswctrl, usb=usb)
        return _server.start()


def stop_unix_socket_server():
    with _server_lock:
        if _server is not None:
            _server.stop()


def _error_response(request_id, message):
    return {
        "id": request_id,
        "ok": False,
        "error": message,
    }
