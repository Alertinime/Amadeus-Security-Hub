import os
import wmi


class key_listing_win:
    def __init__(self):
        self.client = wmi.WMI()

    def check_for_key(self):
        usblist = []
        for disk in self.client.Win32_LogicalDisk():
            if disk.DriveType == 2:
                usblist.append(disk)
        if len(usblist) != 0:
            return usblist
        return False

    def _get_disk_drive(self, usb):
        try:
            partitions = usb.associators(wmi_result_class="Win32_DiskPartition")
        except Exception:
            return None

        for partition in partitions:
            try:
                drives = partition.associators(wmi_result_class="Win32_DiskDrive")
            except Exception:
                continue
            for drive in drives:
                return drive
        return None

    def get_usb_name(self, usb):
        drive = self._get_disk_drive(usb)
        if drive is None:
            return usb.Caption

        for attr in ("Model", "Caption", "Name"):
            value = getattr(drive, attr, None)
            if isinstance(value, str):
                value = value.strip()
                if value:
                    return value
        return usb.Caption

    def list_usb_for_frontend(self):
        usblist = self.check_for_key()
        if usblist == False:
            return []
        return [{"id": usb.Caption, "name": self.get_usb_name(usb)} for usb in usblist]

    def check_for_security_key(self,usbl):
        for usb in usbl:
            if os.path.exists(os.path.join(usb.Caption, "USBSecurity", "USBKey.json")):
                return usb
        return False
