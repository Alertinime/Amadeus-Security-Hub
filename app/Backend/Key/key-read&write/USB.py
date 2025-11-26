import os
import base64
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import hashlib
import tkinter as tk
from argon2.low_level import hash_secret_raw, Type
import uuid
import json
import ctypes
from gc import collect
class USB:
    def __init__(self, usb_path):
        self.usb = usb_path
    def is_usb(self):
        if not os.path.exists(self.usb.caption):
            print(f"USB path {self.usb.caption} does not exist.")
            return False
        return True
    def charging(self):
        if not self.is_usb():
            return
    def doK(self):
        salt = hashlib.sha256(self.usb.VolumeSerialNumber.encode()).digest()[:16]
        pss = self.get_processed()
        fin = pss
        kdf = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt, 
            info=b"fixed-app-context"
        )
        fk = kdf.derive(fin)
        collect()
        return fk
    def run_create(self):
        if not self.is_usb():
            return
        self.charging()
        potato = self.doK()
        encrypted = self.prepare_data(potato)
        if self.save(encrypted):
            print("USBKey created successfully.")
        else:
            print("Device already an usbkey. Abording creation.")

    def run_decrypt(self):
        if not self.is_usb():
            return
        self.charging()
        potato = self.doK()
        data = self.get_data(potato)
        print("USBKey decrypted successfully.")
        return data
    
    
    def get_data(self,potato):
        path = os.path.join(self.usb.Caption, "USBSecurity", "USBKey.json")
        if os.path.exists(path):
            with open(path, 'r') as f:
                data = json.load(f)
            iv = base64.b64decode(data['iv'])
            ciphertext = base64.b64decode(data['data'])
            aesgcm = AESGCM(potato)
            plaintext = aesgcm.decrypt(iv, ciphertext, None)
            return json.loads(plaintext.decode())
        return False
    
    def save(self, data):
        path = os.path.join(self.usb.Caption, "USBSecurity")
        if not os.path.exists(path):
            os.makedirs(path)
            with open(os.path.join(path, "USBKey.json"), 'w') as f:
                json.dump(data, f, indent=4)
            FILE_ATTRIBUTE_HIDDEN = 0x02
            attrs = ctypes.windll.kernel32.GetFileAttributesW(path)
            new_attrs = attrs | FILE_ATTRIBUTE_HIDDEN
            ctypes.windll.kernel32.SetFileAttributesW(path, new_attrs)
            attrs = ctypes.windll.kernel32.GetFileAttributesW(path)
            is_hidden = bool(attrs & 0x02)
            print("Hidden:", is_hidden)
            return True
        return False
    def prepare_data(self,potato):
        Uk = os.urandom(32)
        data =  {"UUID": str(uuid.uuid4()), "key": base64.b64encode(Uk).decode()}
        json_bytes = json.dumps(data, separators=(',', ':')).encode()
        aesgcm = AESGCM(potato)
        iv = os.urandom(12)
        ciphertext = aesgcm.encrypt(iv, json_bytes, None)
        encrypted_package = {
            "iv": base64.b64encode(iv).decode(),
            "data": base64.b64encode(ciphertext).decode()
        }
        return encrypted_package
    def get_processed(self):
        def confirmer():
            pss = entry.get().encode()
            salt = hashlib.sha256(self.usb.VolumeSerialNumber.encode()).digest()[:16]
            pk = hash_secret_raw(
                secret=pss,
                salt=salt,
                time_cost=5,
                memory_cost=262144,
                parallelism=4,
                hash_len=32,
                type=Type.ID
            )
            self.result = pk
            root.destroy()

        if tk._default_root is None:
            root = tk.Tk()
            nmr = True
        else:
            root = tk.Toplevel()
            nmr = False
        root.title("Mot de passe")

        entry = tk.Entry(root, show="*")
        entry.pack()
        tk.Button(root, text="Confirmer", command=confirmer).pack()
        if nmr:
            root.mainloop()
        else:
            root.wait_window()
        return self.result