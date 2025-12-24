import tkinter as tk
from config import COLOR_BG_MEDIUM, COLOR_ACCENT, COLOR_TEXT_PRIMARY
import hashlib
import base64
import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

class TooltipButton(tk.Button):
    def __init__(self, parent, text, emoji, tooltip_text="", **kwargs):
        super().__init__(parent, text=emoji, font=("Segoe UI", 10), bg=COLOR_BG_MEDIUM, fg=COLOR_ACCENT, relief="flat", cursor="hand2", width=3, **kwargs)
        
        self.tooltip_text = tooltip_text
        self.tooltip = None
        self.bind("<Enter>", self._show_tooltip)
        self.bind("<Leave>", self._hide_tooltip)
    
    def _show_tooltip(self, event):
        if not self.tooltip_text:
            return
        
        self.tooltip = tk.Toplevel(self)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_attributes("-topmost", True)
        
        label = tk.Label(self.tooltip, text=self.tooltip_text, bg="#333333", fg=COLOR_TEXT_PRIMARY, padx=5, pady=2, font=("Segoe UI", 8))
        label.pack()
        
        x = event.x_root - 10
        y = event.y_root - 30
        self.tooltip.wm_geometry(f"+{x}+{y}")
    
    def _hide_tooltip(self, event):
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None

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