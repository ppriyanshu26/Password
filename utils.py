import hashlib
import base64
import os
import tkinter as tk
import win32gui
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

class Btn:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip_window = None
        widget.bind("<Enter>", self.show)
        widget.bind("<Leave>", self.hide)

    def show(self, event=None):
        if self.tip_window:
            return
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + 20
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        tw.attributes("-topmost", True)
        label = tk.Label(tw, text=self.text, bg="#333", fg="white", relief="solid", borderwidth=1, font=("Segoe UI", 9), padx=6, pady=2)
        label.pack()

    def hide(self, event=None):
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None

def get_window_title():
    hwnd = win32gui.GetForegroundWindow()
    return win32gui.GetWindowText(hwnd)
