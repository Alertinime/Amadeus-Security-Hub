import re


_USBSTOR_RE = re.compile(r"USBSTOR\\[^\\]+\\([^\\]+)", re.IGNORECASE)


def normalize_usb_serial(value) -> str:
    if value is None:
        return ""

    if not isinstance(value, str):
        value = str(value)

    value = value.strip().strip("\x00")
    if not value:
        return ""

    usbstor_match = _USBSTOR_RE.search(value)
    if usbstor_match:
        value = usbstor_match.group(1)

    if "\\" in value:
        value = value.rstrip("\\").split("\\")[-1]

    if "&" in value:
        head, tail = value.rsplit("&", 1)
        if tail.isdigit():
            value = head

    return value.strip().strip("\x00")
