import os
from cryptography.hazmat.primitives.kdf.argon2 import Argon2id
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
    def create_salt(self):
        salt = os.urandom(16)
        return salt