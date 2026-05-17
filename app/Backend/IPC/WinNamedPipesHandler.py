import json
import threading

import pywintypes
import win32api
import win32file
import win32pipe
import win32security

from Backend.Controller.AMHSPswdCtrl import Pswctrl
PIPE_NAME = r"\\.\pipe\amadeus-security-hub"
BUFFER_SIZE = 64 * 1024
ERROR_BROKEN_PIPE = 109
ERROR_MORE_DATA = 234
ERROR_NO_DATA = 232
ERROR_PIPE_CONNECTED = 535

_server = None
_server_lock = threading.Lock()


class NamedPipeServer:
    def __init__(self, pipe_name=PIPE_NAME, passwordctrl=None, usb=None):
        self.pipe_name = pipe_name
        self._stop_event = threading.Event()
        self._thread = None
        self._current_pipe = None
        self.passctrl = passwordctrl
        self.usb = usb

    def start(self):
        if self.is_running():
            return False

        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._serve_forever,
            name="AmadeusNamedPipeServer",
            daemon=True,
        )
        self._thread.start()
        return True

    def stop(self):
        self._stop_event.set()
        self._close_current_pipe()

    def is_running(self):
        return self._thread is not None and self._thread.is_alive()

    def _serve_forever(self):
        while not self._stop_event.is_set():
            pipe = None
            try:
                pipe = self._create_pipe()
                self._current_pipe = pipe
                self._wait_for_client(pipe)
                self._handle_client(pipe)
            except pywintypes.error as exc:
                if not self._stop_event.is_set():
                    print("Named pipe server error:", exc)
            finally:
                self._disconnect_and_close(pipe)
                self._current_pipe = None

    def _create_pipe(self):
        return win32pipe.CreateNamedPipe(
            self.pipe_name,
            win32pipe.PIPE_ACCESS_DUPLEX,
            win32pipe.PIPE_TYPE_MESSAGE
            | win32pipe.PIPE_READMODE_MESSAGE
            | win32pipe.PIPE_WAIT,
            1,
            BUFFER_SIZE,
            BUFFER_SIZE,
            0,
            _current_user_security_attributes(),
        )

    def _wait_for_client(self, pipe):
        try:
            win32pipe.ConnectNamedPipe(pipe, None)
        except pywintypes.error as exc:
            if exc.winerror != ERROR_PIPE_CONNECTED:
                raise

    def _handle_client(self, pipe):
        while not self._stop_event.is_set():
            try:
                payload = self._read_message(pipe)
            except pywintypes.error as exc:
                if exc.winerror in (ERROR_BROKEN_PIPE, ERROR_NO_DATA):
                    break
                raise

            if payload is None:
                break

            response = self._dispatch(payload)
            self._write_message(pipe, response)

    def _read_message(self, pipe):
        chunks = []

        while True:
            result, data = win32file.ReadFile(pipe, BUFFER_SIZE)
            chunks.append(data)
            if result == ERROR_MORE_DATA:
                continue
            if result == 0:
                break

        if not chunks:
            return None

        try:
            return json.loads(b"".join(chunks).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            return {
                "__ipc_error": f"Invalid JSON message: {exc}",
            }

    def _write_message(self, pipe, response):
        win32file.WriteFile(pipe, json.dumps(response).encode("utf-8"))

    def _dispatch(self, payload):
        request_id = payload.get("id") if isinstance(payload, dict) else None

        if not isinstance(payload, dict):
            return _error_response(request_id, "Message must be a JSON object")
        if "__ipc_error" in payload:
            return _error_response(request_id, payload["__ipc_error"])

        message_type = payload.get("type")
        if message_type == "Ask":

            return {
                "id": request_id,
                "type": "password_response",
                "value": self.getPasswordByDomaine(payload.get("cible")),
            }

        return _error_response(request_id, f"Unsupported message type: {message_type}")

    def getPasswordByDomaine(self, domaine):
        if self.passctrl is None or self.usb is None:
            return None

        try:
            return self.passctrl.get_password_by_domaine(self.usb, domaine)
        except Exception as exc:
            print(f"Error retrieving password for domaine '{domaine}': {exc}")
            return None

        return None
    def _disconnect_and_close(self, pipe):
        if pipe is None:
            return

        try:
            win32pipe.DisconnectNamedPipe(pipe)
        except pywintypes.error:
            pass
        try:
            win32file.CloseHandle(pipe)
        except pywintypes.error:
            pass

    def _close_current_pipe(self):
        if self._current_pipe is None:
            return

        try:
            win32file.CloseHandle(self._current_pipe)
        except pywintypes.error:
            pass


def start_named_pipe_server(pswctrl,usb):
    global _server
    with _server_lock:
        if _server is None:
            _server = NamedPipeServer(passwordctrl=pswctrl, usb=usb)
        return _server.start()


def stop_named_pipe_server():
    with _server_lock:
        if _server is not None:
            _server.stop()


def NamedPipesHandler():
    start_named_pipe_server()


def _error_response(request_id, message):
    return {
        "id": request_id,
        "ok": False,
        "error": message,
    }


def _current_user_security_attributes():
    security_attributes = pywintypes.SECURITY_ATTRIBUTES()
    security_descriptor = win32security.SECURITY_DESCRIPTOR()
    security_descriptor.Initialize()

    user_sid, _, _ = win32security.LookupAccountName(None, win32api.GetUserName())
    dacl = win32security.ACL()
    dacl.AddAccessAllowedAce(
        win32security.ACL_REVISION,
        win32file.GENERIC_READ | win32file.GENERIC_WRITE,
        user_sid,
    )
    security_descriptor.SetSecurityDescriptorDacl(True, dacl, False)
    security_attributes.SECURITY_DESCRIPTOR = security_descriptor
    return security_attributes
