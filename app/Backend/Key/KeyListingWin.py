import wmi
import os

def check_for_key():
    c = wmi.WMI()
    usblist = []
    for disk in c.Win32_LogicalDisk():
        if disk.DriveType == 2:
            usblist.append(disk)
    if len(usblist) != 0:         
        return usblist
    return False
def check_for_security_key(usbl):
    for usb in usbl:
        if os.path.exists(os.path.join(usb.Caption, "USBSecurity", "USBKey.json")):
            return usb
    return False