
import os



class SecretManager:
    def __init__(self):
        self.secrets_dict = {}

    def generate_random_key(self):
        return os.urandom(32)
    def generate_salt(self):
        return os.urandom(32)
    def store_secret(self, key, secret):
        self.secrets_dict[key] = secret
    def generate_aad(self):
        return os.urandom(16)
