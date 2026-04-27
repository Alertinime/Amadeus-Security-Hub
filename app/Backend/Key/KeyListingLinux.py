import os
import subprocess
from typing import List, Dict, Any
from Backend.Cryptography.PasswordManager import PasswordManager
import base64
import json
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from Backend.Cryptography.SecretManager import SecretManager

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
                    mnt = self._decode_mount_path(parts[1]) if len(parts) > 1 else ""
                    for b in block_names:
                        if dev.startswith(f"/dev/{b}"):
                            mounts.append(mnt)
                            break
        except OSError:
            pass
        return mounts

    def _decode_mount_path(self, path: str) -> str:
        return (
            path.replace("\\040", " ")
            .replace("\\011", "\t")
            .replace("\\012", "\n")
            .replace("\\134", "\\")
        )

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

    def _security_key_path(self, mount_point: str) -> str:
        usbs_dir = os.path.join(mount_point, "USBSecurity")
        return os.path.join(usbs_dir, "USBKey.rin")

    def get_security_dir(self, usb: Dict[str, Any]) -> str:
        key_path = usb.get("security_key_path", "")
        if isinstance(key_path, str) and key_path.strip():
            return os.path.dirname(key_path)

        security_mount = usb.get("security_mount", "")
        if isinstance(security_mount, str) and security_mount.strip():
            return os.path.join(security_mount, "USBSecurity")

        mounts = usb.get("mounts", [])
        if mounts:
            first_mount = mounts[0]
            if isinstance(first_mount, str) and first_mount.strip():
                return os.path.join(first_mount, "USBSecurity")

        return ""

    def get_usb_name(self, usb: Dict[str, Any]) -> str:
        for key in ("product", "manufacturer", "sysname"):
            value = usb.get(key, "")
            if isinstance(value, str) and value.strip():
                return value.strip()
        return "Unknown USB"

    def get_usb_id(self, usb: Dict[str, Any]) -> str:
        for key in ("serial", "sysname"):
            value = usb.get(key, "")
            if isinstance(value, str) and value.strip():
                return value.strip()

        product_id = usb.get("idProduct", "")
        vendor_id = usb.get("idVendor", "")
        if vendor_id or product_id:
            return f"{vendor_id}:{product_id}"

        return self.get_usb_name(usb)

    def get_usb_serial(self, usb: Dict[str, Any]) -> str:
        if not isinstance(usb, dict):
            return ""

        serial = usb.get("serial", "")
        if serial is None:
            return ""
        if not isinstance(serial, str):
            serial = str(serial)
        return serial.strip()

    def list_usb_for_frontend(self) -> List[Dict[str, str]]:
        return [
            {"id": self.get_usb_id(usb), "name": self.get_usb_name(usb)}
            for usb in self.list_usb()
        ]

    def _mount_from_security_dir(self, security_dir: str) -> str:
        security_dir = os.path.realpath(os.path.abspath(security_dir))
        if os.path.basename(security_dir) == "USBSecurity":
            return os.path.dirname(security_dir)
        return security_dir

    def get_usb_from_security_dir(self, security_dir):
        if not isinstance(security_dir, str) or not security_dir.strip():
            return None

        target_security_dir = os.path.realpath(os.path.abspath(security_dir))
        target_mount = self._mount_from_security_dir(target_security_dir)

        for usb in self.list_usb():
            mounts = self._ensure_mounts(usb)
            for mnt in mounts:
                normalized_mount = os.path.realpath(os.path.abspath(mnt))
                normalized_security_dir = os.path.realpath(
                    os.path.join(normalized_mount, "USBSecurity")
                )
                if (
                    normalized_mount == target_mount
                    or normalized_security_dir == target_security_dir
                ):
                    usb["security_mount"] = mnt
                    usb["security_key_path"] = os.path.join(
                        mnt, "USBSecurity", "USBKey.rin"
                    )
                    return usb

            self._release_usb_mounts(usb)

        return None

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
                candidate = self._security_key_path(mnt)
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
            usb["security_mount"] = mnt
            usb["security_key_path"] = os.path.join(usbs_dir, "USBKey.rin")
            return self.make_master_file(usb, hkdf_key, salt)

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
        secret = SecretManager()
        psw_pswManager = secret.generate_random_key()
        if not isinstance(psw_pswManager, (bytes, bytearray)) or len(psw_pswManager) != 32:
            print("Invalid PasswordManagerKey generated for USB:", usb.get("product", "Unknown"))
            return False
        payload_dict = {
            "PasswordManagerKey": base64.b64encode(psw_pswManager).decode("ascii")
        }
        payload = json.dumps(payload_dict).encode("utf-8")
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
            if not self.make_passwordManager_file(usb, psw_pswManager):
                print("Failed to create password manager file for USB:", usb.get("product", "Unknown"))
                return False
            with open(key_path, "w", encoding="utf-8") as f:
                json.dump(package, f, indent=2)
            print("Master file created at:", key_path)
            return True
        except OSError as exc:
            print("Failed to create master file at:", key_path, "Error:", exc)
            return False
    def _normalize_password_entries(self, passwords):
        if passwords is None:
            return []
        if not isinstance(passwords, list):
            return None

        normalized_entries = []
        for entry in passwords:
            if isinstance(entry, dict):
                url = entry.get("url", entry.get("site", entry.get("website", "")))
                password = entry.get("password", entry.get("pass", entry.get("secret", "")))
            elif isinstance(entry, (list, tuple)) and len(entry) == 2:
                url, password = entry
            else:
                return None

            if not isinstance(url, str) or not isinstance(password, str):
                return None

            normalized_entries.append({
                "url": url,
                "password": password,
            })

        return normalized_entries
    def make_passwordManager_file(self, usb: Dict[str, Any], password_manager_key: bytes, passwords=None) -> bool:
        mnt = usb.get("security_mount")
        if not mnt:
            mounts = list(usb.get("mounts", []))
            if mounts:
                mnt = mounts[0]
        if not mnt:
            print("No security mount found for USB:", usb.get("product", "Unknown"))
            return False

        if not isinstance(password_manager_key, (bytes, bytearray)) or len(password_manager_key) != 32:
            print("Invalid PasswordManagerKey provided for USB:", usb.get("product", "Unknown"))
            return False

        password_entries = self._normalize_password_entries(passwords)
        if password_entries is None:
            print("Invalid password list provided for USB:", usb.get("product", "Unknown"))
            return False

        usbs_dir = os.path.join(mnt, "USBSecurity")
        key_path = os.path.join(usbs_dir, "PasswordManager.Archer")
        nonce = os.urandom(12)
        aesgcm = AESGCM(bytes(password_manager_key))
        payload_dict = {
            "sites": password_entries
        }
        aad = usb.get("serial", "").encode("utf-8")
        ciphertext = aesgcm.encrypt(nonce, json.dumps(payload_dict).encode("utf-8"), aad)

        package = {
            "header": {
                "version": 1,
                "type": "security-hub-password-manager",
                "cipher": "AES-256-GCM",
                "key_source": "PasswordManagerKey",
                "payload_format": "site-password-list",
                "nonce": base64.b64encode(nonce).decode("ascii"),
            },
            "payload": base64.b64encode(ciphertext).decode("ascii"),
        }

        try:
            os.makedirs(usbs_dir, exist_ok=True)
            with open(key_path, "w", encoding="utf-8") as f:
                json.dump(package, f, indent=2)
            print("Password manager file created at:", key_path)
            return True
        except OSError as exc:
            print("Failed to create password manager file at:", key_path, "Error:", exc)
            return False

    def login_usb(self, usb, password):
        if isinstance(usb, dict):
            security_dir = self.get_security_dir(usb)
            usb_info = usb
        elif isinstance(usb, str):
            security_dir = usb
            usb_info = self.get_usb_from_security_dir(security_dir)
        else:
            print("Invalid USB reference for login:", usb)
            return False

        if not security_dir:
            print("No security directory provided for Linux login.")
            return False

        security_key_path = os.path.join(security_dir, "USBKey.rin")
        if not usb_info:
            print("Unable to find USB device for security directory:", security_dir)
            return False

        print("Attempting login for USB:", self.get_usb_name(usb_info), "using key file:", security_key_path)
        if not os.path.exists(security_key_path):
            print("No valid security key found for USB:", security_dir)
            return False

        try:
            with open(security_key_path, "r", encoding="utf-8") as f:
                package = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            print("Failed to read security key file:", security_key_path, "Error:", exc)
            return False

        header = package.get("header", {})
        payload = package.get("payload", "")
        if not header or not payload:
            print("Invalid package structure in:", security_key_path)
            return False

        salt_b64 = header.get("password_salt")
        nonce_b64 = header.get("nonce")
        if not salt_b64 or not nonce_b64:
            print("Missing salt or nonce in header of:", security_key_path)
            return False

        usb_serial = self.get_usb_serial(usb_info)
        try:
            salt = base64.b64decode(salt_b64)
            nonce = base64.b64decode(nonce_b64)
            ciphertext = base64.b64decode(payload)
            password_manager = PasswordManager()
            key = password_manager.kdf(password, salt)
            hkdf_key = password_manager.HKDF(key, usb_serial, "Master_Key", 32)
            aesgcm = AESGCM(hkdf_key)
            plaintext = aesgcm.decrypt(nonce, ciphertext, usb_serial.encode("utf-8"))
            data = json.loads(plaintext.decode("utf-8"))
        except Exception as exc:
            print("Failed to decrypt security key file:", security_key_path, "Error:", exc)
            return False

        password_manager_key_b64 = data.get("PasswordManagerKey")
        if not password_manager_key_b64:
            print("PasswordManagerKey missing from security key payload:", security_key_path)
            return False

        try:
            password_manager_key = base64.b64decode(password_manager_key_b64, validate=True)
        except Exception as exc:
            print("Invalid PasswordManagerKey in security key payload:", security_key_path, "Error:", exc)
            return False

        if len(password_manager_key) != 32:
            print("Invalid PasswordManagerKey length in security key payload:", security_key_path)
            return False

        print("Login successful for USB:", self.get_usb_name(usb_info))
        return password_manager_key_b64
