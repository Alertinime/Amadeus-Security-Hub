# cette classe est le controller des fonctionnalités liées au gestionnaire de mots de passe
import os
import json
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

class Pswctrl():
    def __init__(self):
        self.secret = None
    def set_secret(self, value):
        self.secret = value
    def read_in_file(self, path):
        key_path = os.path.join(path, "PasswordManager.Archer")
        with open(key_path, "r", encoding="utf-8") as f:
            file = json.load(f)
        
        header = file.get("header", {})
        package = file.get("payload", {})
        
        if not header or not package:
            return False
        return header, package
    def decrypt_file(self, path, aad):
        result = self.read_in_file(path)
        if not result:
            print("Failed to read file for decryption:", path)
            return False
        header, package = result
        if not header or not package:
            print("Failed to read file for encryption:", path)
            return False
        nonce = base64.b64decode(header.get("nonce"))
        if not nonce:
            print("Nonce not found in header for encryption:", path)
            return False
        aesgcm = AESGCM(base64.b64decode(self.secret))
        ciphertext = base64.b64decode(package)
        ciphertext = aesgcm.decrypt(nonce, ciphertext, aad)
        package = json.loads(ciphertext.decode("utf-8"))
        del nonce, aesgcm, ciphertext
        return header,package
    def encrypt_file(self, path, header, data, aad):
        key_path = os.path.join(path, "PasswordManager.Archer")
        nonce = os.urandom(12)
        aesgcm = AESGCM(base64.b64decode(self.secret))
        ciphertext = aesgcm.encrypt(nonce, json.dumps(data).encode("utf-8"), aad)
        header = dict(header)
        header["nonce"] = base64.b64encode(nonce).decode("utf-8")
        package = base64.b64encode(ciphertext).decode("utf-8")
        with open(key_path, "w", encoding="utf-8") as f:
            json.dump({"header": header, "payload": package}, f, indent=4)
        del key_path, nonce, aesgcm, ciphertext
        return True
    def concatenate_file_and_new_data(self, path, aad, new_data):
        response = self.decrypt_file(path, aad)
        if not response:
            print("Failed to decrypt file for concatenation:", path)
            return False
        header, old_data = response
        if not isinstance(old_data, dict):
            print("Decrypted data is not a dictionary for concatenation:", path)
            return False
        if not isinstance(new_data, dict):
            print("New data is not a dictionary for concatenation:", path)
            return False
        if not isinstance(old_data.get("sites"), list):
            print("Old data 'sites' is not a list for concatenation:", path)
            return False
        if not isinstance(new_data.get("sites"), list):
            print("New data 'sites' is not a list for concatenation:", path)
            return False

        old_data["sites"].extend(new_data["sites"])
        return header, old_data
    def update_file_with_new_data(self, path, aad, new_data):
        response = self.concatenate_file_and_new_data(path, aad, new_data)
        if not response:
            print("Failed to concatenate data for update:", path)
            return False
        header, combined_data = response
        result = self.encrypt_file(path, header, combined_data, aad)
        del header, combined_data, response
        return result
    
    def get_file_data(self, path, aad):
        response = self.decrypt_file(path, aad)
        if not response:
            print("Failed to decrypt file for data retrieval:", path)
            return False
        header, package = response
        del header
        return package