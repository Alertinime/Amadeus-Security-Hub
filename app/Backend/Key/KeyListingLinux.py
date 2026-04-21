import os
import subprocess
from typing import List, Dict, Any
from Backend.Cryptography.PasswordManager import PasswordManager
import base64
import json
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class key_listening_linux:
    _managed_partitions = set()

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

    def _find_partitions(self, block_names: List[str]) -> List[str]:
        partitions = set()
        for name in sorted(set(block_names)):
            block_path = os.path.join("/sys/class/block", name)
            if os.path.exists(os.path.join(block_path, "partition")):
                partitions.add(name)
                continue

            try:
                for child in os.listdir(block_path):
                    child_path = os.path.join(block_path, child)
                    if not os.path.isdir(child_path):
                        continue
                    if os.path.exists(os.path.join(child_path, "partition")):
                        partitions.add(child)
            except OSError:
                pass
        return sorted(partitions)

    def _mount_block_device(self, block_name: str) -> bool:
        device_path = f"/dev/{block_name}"
        try:
            result = subprocess.run(
                ["udisksctl", "mount", "-b", device_path],
                capture_output=True,
                text=True,
                check=True,
            )
            output = (result.stdout or result.stderr or "").strip()
            if output:
                print(output)
            return True
        except FileNotFoundError:
            print("udisksctl not found; unable to mount", device_path)
        except subprocess.CalledProcessError as exc:
            output = ((exc.stdout or "") + (exc.stderr or "")).strip()
            if output:
                print(output)
            else:
                print("Failed to mount", device_path)
        return False

    def _unmount_block_device(self, block_name: str) -> bool:
        device_path = f"/dev/{block_name}"
        try:
            result = subprocess.run(
                ["udisksctl", "unmount", "-b", device_path],
                capture_output=True,
                text=True,
                check=True,
            )
            output = (result.stdout or result.stderr or "").strip()
            if output:
                print(output)
            return True
        except FileNotFoundError:
            print("udisksctl not found; unable to unmount", device_path)
        except subprocess.CalledProcessError as exc:
            output = ((exc.stdout or "") + (exc.stderr or "")).strip()
            if output:
                print(output)
            else:
                print("Failed to unmount", device_path)
        return False

    def _security_key_paths(self, mount_point: str) -> List[str]:
        usbs_dir = os.path.join(mount_point, "USBSecurity")
        return [
            os.path.join(usbs_dir, "USBKey.rin"),
            os.path.join(usbs_dir, "USBKey.json"),
        ]

    def _ensure_mounts(self, usb: Dict[str, Any]) -> List[str]:
        mounts = list(usb.get("mounts", []))
        if mounts:
            return mounts

        partitions = list(usb.get("partitions", []))
        mounted_by_app = set(usb.get("mounted_by_app", []))
        if not partitions:
            print("No partitions found for USB:", usb.get("product", "Unknown"))
            return []

        for block_name in partitions:
            if not self._mount_block_device(block_name):
                continue

            mounted_by_app.add(block_name)
            self._managed_partitions.add(block_name)
            mounts = self._mounted_points_for(partitions)
            if mounts:
                usb["mounts"] = mounts
                usb["mounted_by_app"] = sorted(mounted_by_app)
                return mounts

        return []

    def _release_usb_mounts(self, usb: Dict[str, Any]) -> None:
        for block_name in reversed(list(usb.get("mounted_by_app", []))):
            if self._unmount_block_device(block_name):
                self._managed_partitions.discard(block_name)
        usb["mounted_by_app"] = []
        usb["mounts"] = []

    def cleanup_managed_mounts(self) -> None:
        for block_name in sorted(self._managed_partitions, reverse=True):
            if self._unmount_block_device(block_name):
                self._managed_partitions.discard(block_name)

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
            if not blocks:
                continue
            partitions = self._find_partitions(blocks)
            info["partitions"] = partitions
            info["mounts"] = self._mounted_points_for(partitions or blocks)
            devices.append(info)
        return devices
    def check_for_security_key(self, usbl):
        print("Checking for security key in USB devices...")
        for usb in usbl:
            mounts = self._ensure_mounts(usb)
            for mnt in mounts:
                for candidate in self._security_key_paths(mnt):
                    print("Checking for security key at:", candidate)
                    if os.path.exists(candidate):
                        usb["security_mount"] = mnt
                        usb["security_key_path"] = candidate
                        print("Found security key at:", candidate)
                        return usb
            self._release_usb_mounts(usb)
        return False
    def initialize_security_key(self, usb: Dict[str, Any], password: str) -> bool:
        print("Initializing security key for USB:", usb.get("product", "Unknown"))
        mounts = self._ensure_mounts(usb)
        if not mounts:
            print("No mounted filesystem available for USB initialization.")
            return False

        for mnt in mounts:
            usbs_dir = os.path.join(mnt, "USBSecurity")
            pss_mgnr = PasswordManager()
            salt = pss_mgnr.create_salt()
            key = pss_mgnr.kdf(password, salt)
            saltusb = usb.get("serial", "")
            hkdf_key = pss_mgnr.HKDF(key,saltusb,"Master_Key", 32)
            print("Derived key for initialization:", hkdf_key.hex())
            self.make_master_file(usb, hkdf_key, salt)
            return bool(usbs_dir and salt and key)

        return False
    def make_master_file(self, usb: Dict[str, Any], master_key: bytes, saltpasw,) -> bool:


        mnt = usb.get("security_mount")
        if not mnt:
            mounts = list(usb.get("mounts", []))
            if mounts:
                mnt = mounts[0]
        if not mnt:
            print("No security mount found for USB:", usb.get("product", "Unknown"))
            return False

        if not isinstance(master_key, (bytes, bytearray)) or len(master_key) not in (16, 24, 32):
            print("Invalid master key provided for USB:", usb.get("product", "Unknown"))
            return False

        if isinstance(saltpasw, bytes):
            salt_bytes = saltpasw
        elif isinstance(saltpasw, str):
            salt_bytes = saltpasw.encode("utf-8")
        else:
            print("Invalid password salt provided for USB:", usb.get("product", "Unknown"))
            return False

        usbs_dir = os.path.join(mnt, "USBSecurity")
        key_path = os.path.join(usbs_dir, "USBKey.rin")
        usb_serial = usb.get("serial", "")
        nonce = os.urandom(12)
        aesgcm = AESGCM(bytes(master_key))
        payload = b"{}"
        aad = usb_serial.encode("utf-8")
        ciphertext = aesgcm.encrypt(nonce, payload, aad)

        package = {
            "header": {
                "version": 1,
                "type": "security-hub-master",
                "cipher": "AES-256-GCM",
                "kdf": "Argon2id",
                "hkdf_info": "Master_Key",
                "password_salt": base64.b64encode(salt_bytes).decode("ascii"),
                "nonce": base64.b64encode(nonce).decode("ascii"),
            },
            "payload": base64.b64encode(ciphertext).decode("ascii"),
        }

        try:
            os.makedirs(usbs_dir, exist_ok=True)
            with open(key_path, "w", encoding="utf-8") as f:
                json.dump(package, f, indent=2)
            print("Master file created at:", key_path)
            return True
        except OSError as exc:
            print("Failed to create master file at:", key_path, "Error:", exc)
            return False
