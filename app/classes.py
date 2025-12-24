import tkinter as tk
from config import COLOR_BG_MEDIUM, COLOR_ACCENT, COLOR_TEXT_PRIMARY
import hashlib
import base64
import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

class Crypto:
    def __init__(self, key):
        self.key = key
    
    def encrypt_aes(self, plaintext):
        key = hashlib.sha256(self.key.encode()).digest()
        nonce = os.urandom(12)
        aesgcm = AESGCM(key)
        ciphertext = aesgcm.encrypt(nonce, plaintext.encode(), None)
        return base64.urlsafe_b64encode(nonce + ciphertext).decode()

    def decrypt_aes(self, ciphertext):
        try:
            key = hashlib.sha256(self.key.encode()).digest()
            raw = base64.urlsafe_b64decode(ciphertext)
            nonce = raw[:12]
            encrypted_data = raw[12:]
            aesgcm = AESGCM(key)
            plaintext = aesgcm.decrypt(nonce, encrypted_data, None)
            return plaintext.decode()
        except Exception:
            return None