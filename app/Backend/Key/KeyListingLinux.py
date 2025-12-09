import os
import subprocess
from typing import List, Dict, Any
from Backend.Cryptography.PasswordManager import PasswordManager

class key_listening_linux:
    def list_with_lsusb(self) -> List[str]:
        try:
            out = subprocess.check_output(["lsusb"], text=True)
            return [line.strip() for line in out.splitlines() if line.strip()]
        except (FileNotFoundError, subprocess.CalledProcessError):
            return []

    def _find_block_devices(self, devpath: str) -> List[str]:
        blocks = set()
        for root, dirs, _ in os.walk(devpath):
            if "block" in dirs:
                blkdir = os.path.join(root, "block")
                try:
                    for name in os.listdir(blkdir):
                        if name:
                            blocks.add(name)
                except OSError:
                    pass
        return sorted(blocks)

    def _mounted_points_for(self, block_names: List[str]) -> List[str]:
        mounts = []
        try:
            with open("/proc/mounts", "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    parts = line.split()
                    if not parts:
                        continue
                    dev = parts[0]
                    mnt = parts[1] if len(parts) > 1 else ""
                    for b in block_names:
                        if dev.startswith(f"/dev/{b}"):
                            mounts.append(mnt)
                            break
        except OSError:
            pass
        return mounts

    def list_usb(self) -> List[Dict[str, Any]]:
        base = "/sys/bus/usb/devices"
        devices: List[Dict[str, Any]] = []
        if not os.path.isdir(base):
            return devices

        for entry in os.listdir(base):
            path = os.path.join(base, entry)
            if not os.path.isdir(path):
                continue
            idv = os.path.join(path, "idVendor")
            if not os.path.isfile(idv):
                continue
            info: Dict[str, Any] = {}
            for name in ("idVendor", "idProduct", "manufacturer", "product", "serial"):
                try:
                    with open(os.path.join(path, name), "r", encoding="utf-8", errors="ignore") as f:
                        info[name] = f.read().strip()
                except FileNotFoundError:
                    info[name] = ""
            info["sysname"] = entry
            blocks = self._find_block_devices(path)
            info["blocks"] = blocks
            info["mounts"] = self._mounted_points_for(blocks)
            if not blocks:
                continue
            devices.append(info)
        return devices
    def check_for_security_key(self, usbl):
        for usb in usbl:
            for mnt in usb.get("mounts", []):
                candidate = os.path.join(mnt, "USBSecurity", "USBKey.json")
                if os.path.exists(candidate):
                    usb["security_mount"] = mnt
                    usb["security_key_path"] = candidate
                    print("Found security key at:", candidate)
                    return usb
        return False
    def initialize_security_key(self, usb: Dict[str, Any], password: str) -> bool:
        for mnt in usb.get("mounts", []):
            usbs_dir = os.path.join(mnt, "USBSecurity")
            pss_mgnr = PasswordManager()
            salt = pss_mgnr.create_salt()
            key = pss_mgnr.kdf(password, salt)