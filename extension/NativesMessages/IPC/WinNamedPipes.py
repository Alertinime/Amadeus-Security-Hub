import json

import pywintypes
import win32file
import win32pipe


PIPE_NAME = r"\\.\pipe\amadeus-security-hub"
BUFFER_SIZE = 64 * 1024
ERROR_MORE_DATA = 234


class WinNamedPipes:
    def __init__(self, pipe_name=PIPE_NAME, timeout_ms=3000):
        self.pipe_name = pipe_name
        self.timeout_ms = timeout_ms

    def request(self, message):
        pipe = self._connect()
        try:
            self._write_message(pipe, message)
            return self._read_message(pipe)
        finally:
            win32file.CloseHandle(pipe)

    def _connect(self):
        win32pipe.WaitNamedPipe(self.pipe_name, self.timeout_ms)
        pipe = win32file.CreateFile(
            self.pipe_name,
            win32file.GENERIC_READ | win32file.GENERIC_WRITE,
            0,
            None,
            win32file.OPEN_EXISTING,
            0,
            None,
        )
        win32pipe.SetNamedPipeHandleState(
            pipe,
            win32pipe.PIPE_READMODE_MESSAGE,
            None,
            None,
        )
        return pipe

    def _write_message(self, pipe, message):
        encoded = json.dumps(message).encode("utf-8")
        win32file.WriteFile(pipe, encoded)

    def _read_message(self, pipe):
        chunks = []

        while True:
            result, data = win32file.ReadFile(pipe, BUFFER_SIZE)
            chunks.append(data)
            if result == ERROR_MORE_DATA:
                continue
            if result == 0:
                break

        return json.loads(b"".join(chunks).decode("utf-8"))


def pipe_request(message):
    try:
        return WinNamedPipes().request(message)
    except pywintypes.error as exc:
        return {
            "id": message.get("id") if isinstance(message, dict) else None,
            "ok": False,
            "error": f"pipe_unavailable: {exc}",
        }
