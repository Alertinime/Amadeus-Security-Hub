import os
import wmi
from Backend.Cryptography.PasswordManager import PasswordManager
import base64
import json
from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from Backend.Cryptography.SecretManager import SecretManager
from Backend.Key.USBIdentity import normalize_usb_serial

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

    def _get_usb_root(self, usb):
        mount = getattr(usb, "Caption", "") or getattr(usb, "DeviceID", "")
        if not isinstance(mount, str):
            return ""
        mount = mount.strip().rstrip("\\/")
        if len(mount) == 2 and mount[1] == ":":
            return mount + "\\"
        return mount

    def get_security_dir(self, usb):
        root = self._get_usb_root(usb)
        if not root:
            return ""
        return os.path.join(root, "USBSecurity")

    def _security_key_path(self, usb):
        usbs_dir = self.get_security_dir(usb)
        if not usbs_dir:
            return ""
        return os.path.join(usbs_dir, "USBKey.rin")

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

    def get_usb_serial(self, usb):
        drive = self._get_disk_drive(usb)

        for source, attrs in (
            (drive, ("SerialNumber", "PNPDeviceID", "DeviceID")),
            (usb, ("VolumeSerialNumber", "DeviceID", "Caption")),
        ):
            if source is None:
                continue
            for attr in attrs:
                value = getattr(source, attr, None)
                if value is None:
                    continue
                if not isinstance(value, str):
                    value = str(value)
                serial = normalize_usb_serial(value)
                if serial:
                    return serial

        return ""

    def list_usb_for_frontend(self):
        usblist = self.check_for_key()
        if usblist == False:
            return []
        return [{"id": usb.Caption, "name": self.get_usb_name(usb)} for usb in usblist]

    def check_for_security_key(self,usbl):
        for usb in usbl:
            key_path = self._security_key_path(usb)
            if key_path and os.path.exists(key_path):
                return usb
        return False

    def initialize_security_key(self, usb, password):
        print("Initializing security key for USB:", self.get_usb_name(usb))
        root = self._get_usb_root(usb)
        if not root:
            print("No USB root found for:", self.get_usb_name(usb))
            return False

        usbs_dir = os.path.join(root, "USBSecurity")
        try:
            os.makedirs(usbs_dir, exist_ok=True)
        except OSError as exc:
            print("Failed to create USBSecurity directory:", exc)
            return False

        pss_mgnr = PasswordManager()
        salt = pss_mgnr.create_salt()
        key = pss_mgnr.kdf(password, salt)
        saltusb = self.get_usb_serial(usb)
        hkdf_key = pss_mgnr.HKDF(key, saltusb, "Master_Key", 32)
        print("Derived key for initialization:", hkdf_key.hex())
        return self.make_master_file(usb, hkdf_key, salt)
    
    def make_master_file(self, usb, master_key, saltpasw):
        root = self._get_usb_root(usb)
        if not root:
            print("No security root found for USB:", self.get_usb_name(usb))
            return False

        if not isinstance(master_key, (bytes, bytearray)) or len(master_key) not in (16, 24, 32):
            print("Invalid master key provided for USB:", self.get_usb_name(usb))
            return False

        if isinstance(saltpasw, bytes):
            salt_bytes = saltpasw
        elif isinstance(saltpasw, str):
            salt_bytes = saltpasw.encode('utf-8')
        else:
            print("Invalid salt type provided for USB:", self.get_usb_name(usb))
            return False

        usbs_dir = os.path.join(root, "USBSecurity")
        key_path = os.path.join(usbs_dir, "USBKey.rin")
        usb_serial = self.get_usb_serial(usb)
        nonce = os.urandom(12)
        aesgcm = AESGCM(bytes(master_key))
        secret = SecretManager()
        psw_pswManager = secret.generate_random_key()
        if not isinstance(psw_pswManager, (bytes, bytearray)) or len(psw_pswManager) != 32:
            print("Invalid PasswordManagerKey generated for USB:", self.get_usb_name(usb))
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
                print("Failed to create password manager file for USB:", self.get_usb_name(usb))
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
    def make_passwordManager_file(self, usb, password_manager_key, passwords=None):
        root = self._get_usb_root(usb)
        if not root:
            print("No security root found for USB:", self.get_usb_name(usb))
            return False

        if not isinstance(password_manager_key, (bytes, bytearray)) or len(password_manager_key) != 32:
            print("Invalid PasswordManagerKey provided for USB:", self.get_usb_name(usb))
            return False

        password_entries = self._normalize_password_entries(passwords)
        if password_entries is None:
            print("Invalid password list provided for USB:", self.get_usb_name(usb))
            return False

        usbs_dir = os.path.join(root, "USBSecurity")
        key_path = os.path.join(usbs_dir, "PasswordManager.Archer")
        nonce = os.urandom(12)
        aesgcm = AESGCM(bytes(password_manager_key))
        payload_dict = {
            "sites": password_entries
        }
        aad = self.get_usb_serial(usb).encode("utf-8")
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
    def get_usb_from_security_dir(self, security_dir):
        if not isinstance(security_dir, str) or not security_dir.strip():
            return None

        drive, _ = os.path.splitdrive(os.path.abspath(security_dir))
        if not drive:
            return None

        device_id = drive.rstrip("\\/")
        disks = self.client.Win32_LogicalDisk(DeviceID=device_id)
        if not disks:
            return None

        usb = disks[0]
        if getattr(usb, "DriveType", None) != 2:
            return None

        return usb
    def login_usb(self, usb, password,):

        password_manager = PasswordManager()
        security_key_path = os.path.join(usb, "USBKey.rin")
        usb = self.get_usb_from_security_dir(usb)
        print("Attempting login for USB:", usb, "using key file:", security_key_path)
        if security_key_path and os.path.exists(security_key_path):
            with open(security_key_path, "r", encoding="utf-8") as f:
                package = json.load(f)
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

            salt = base64.b64decode(salt_b64)
            nonce = base64.b64decode(nonce_b64)
            key = password_manager.kdf(password, salt)
            usb_serial = self.get_usb_serial(usb)
            hkdf_key = password_manager.HKDF(key, usb_serial, "Master_Key", 32)
            aesgcm = AESGCM(hkdf_key)
            ciphertext = base64.b64decode(payload)
            aad = usb_serial.encode("utf-8")
            print("Decrypt debug:", {"file": security_key_path, "usb_serial": usb_serial, "aad_hex": aad.hex(), "password_salt_b64": salt_b64, "password_salt_hex": salt.hex(), "nonce_b64": nonce_b64, "nonce_hex": nonce.hex(), "hkdf_key_hex": hkdf_key.hex(), "ciphertext_len": len(ciphertext), "payload_b64_len": len(payload)})
            try:
                ciphertext = aesgcm.decrypt(nonce, ciphertext, aad)
            except InvalidTag:
                print(
                    "Failed to decrypt security key file:",
                    security_key_path,
                    "Error: InvalidTag",
                    "USB serial:",
                    usb_serial,
                )
                return False
            package = json.loads(ciphertext.decode("utf-8"))
            password_manager_key_b64 = package.get("PasswordManagerKey")

            print("Login successful for USB:", self.get_usb_name(usb))

            return password_manager_key_b64

        print("No valid security key found for USB:", usb)
        return False
    def get_file_header(self, file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                package = json.load(f)
            return package.get("header", {})
        except (OSError, json.JSONDecodeError) as exc:
            print("Failed to read or parse file header from:", file_path, "Error:", exc)
            return {}
