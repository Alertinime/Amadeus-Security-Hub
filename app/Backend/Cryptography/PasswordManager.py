import os
from cryptography.hazmat.primitives.kdf.argon2 import Argon2id
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes
import hashlib
class PasswordManager:
    def _init_(self):
        pass

    def kdf(self, mdp, salt):
        kdf = Argon2id(
            length=32,
            salt= salt,
            iterations=1,
            memory_cost=2_097_152,
            lanes=8,
        )
        key = kdf.derive(mdp.encode())
        return key
    def HKDF(self, key_material,salt, info, length):
        hkdf = HKDF(
            algorithm=hashes.SHA256(),
            length=length,
            salt=hashlib.sha256(salt.encode()).digest(),
            info=info.encode(),
        )
        derived_key = hkdf.derive(key_material)
        return derived_key
    def create_salt(self):
        salt = os.urandom(16)
        return salt