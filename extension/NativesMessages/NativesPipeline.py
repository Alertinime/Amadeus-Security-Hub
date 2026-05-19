#!/usr/bin/env python3
import json
import os
import struct
import sys
import uuid


def _load_pipe_request():
    if os.name == "nt":
        from IPC.WinNamedPipes import pipe_request

        return pipe_request

    if os.name == "posix":
        from IPC.LinuxUnixSocket import pipe_request

        return pipe_request

    def unsupported_os_request(message):
        return {
            "id": message.get("id") if isinstance(message, dict) else None,
            "ok": False,
            "error": f"unsupported_os: {os.name}",
        }

    return unsupported_os_request


pipe_request = _load_pipe_request()


def read_message():
    raw_length = sys.stdin.buffer.read(4)

    if len(raw_length) == 0:
        return None

    if len(raw_length) < 4:
        raise RuntimeError("Incomplete Native Messaging header")

    message_length = struct.unpack("<I", raw_length)[0]
    raw_message = sys.stdin.buffer.read(message_length)

    if len(raw_message) < message_length:
        raise RuntimeError("Incomplete Native Messaging payload")

    return json.loads(raw_message.decode("utf-8"))


def send_message(message):
    encoded = json.dumps(message).encode("utf-8")
    sys.stdout.buffer.write(struct.pack("<I", len(encoded)))
    sys.stdout.buffer.write(encoded)
    sys.stdout.buffer.flush()


def main():
    while True:
        message = read_message()

        if message is None:
            break

        if not isinstance(message, dict):
            send_message({
                "ok": False,
                "error": "message_must_be_object",
            })
            continue

        message.setdefault("id", str(uuid.uuid4()))
        send_message(pipe_request(message))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        # Keep stdout reserved for the Native Messaging protocol.
        print(f"Native host error: {e}", file=sys.stderr)
