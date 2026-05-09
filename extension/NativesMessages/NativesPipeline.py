#!/usr/bin/env python3
import sys
import json
import struct


def read_message():
    raw_length = sys.stdin.buffer.read(4)

    if len(raw_length) == 0:
        return None

    if len(raw_length) < 4:
        raise RuntimeError("Header incomplet")

    message_length = struct.unpack("@I", raw_length)[0]

    raw_message = sys.stdin.buffer.read(message_length)

    if len(raw_message) < message_length:
        raise RuntimeError("Message incomplet")

    return json.loads(raw_message.decode("utf-8"))

def send_message(message):
    encoded = json.dumps(message).encode("utf-8")
    sys.stdout.buffer.write(struct.pack("@I", len(encoded)))
    sys.stdout.buffer.write(encoded)
    sys.stdout.buffer.flush()


def main():
    while True:
        message = read_message()

        if message is None:
            break

        # Exemple de traitement
        if message.get("type") == "ping":
            send_message({
                "type": "pong",
                "ok": True
            })

        elif message.get("type") == "get_status":
            send_message({
                "type": "status",
                "locked": True,
                "app": "Security Hub"
            })

        else:
            send_message({
                "type": "error",
                "error": "unknown_message_type"
            })


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        # IMPORTANT : jamais de print() sur stdout.
        # stdout est réservé au protocole Native Messaging.
        print(f"Native host error: {e}", file=sys.stderr)