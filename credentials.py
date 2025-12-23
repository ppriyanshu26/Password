import json
import os
import hashlib
from config import VAULT_FILE, MASTER_KEY_PATH

def hash_master_key(key):
    return hashlib.sha256(key.encode('utf-8')).hexdigest()

def save_master_key(key):
    hashed = hash_master_key(key)
    with open(MASTER_KEY_PATH, "w", encoding="utf-8") as f:
        f.write(hashed)

def verify_master_key(key):
    if not os.path.exists(MASTER_KEY_PATH):
        return False  
    with open(MASTER_KEY_PATH, "r", encoding="utf-8") as f:
        stored_hash = f.read().strip()    
    return hash_master_key(key) == stored_hash

def master_key_exists():
    return os.path.exists(MASTER_KEY_PATH)

def load_vault():
    if not os.path.exists(VAULT_FILE):
        return {}    
    with open(VAULT_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_vault(vault):
    with open(VAULT_FILE, "w", encoding="utf-8") as f:
        json.dump(vault, f, indent=2, ensure_ascii=False)

class CredentialVault:
    def __init__(self, crypto=None):
        self.crypto = crypto
        self.vault = load_vault()
    
    def set_crypto(self, crypto):
        self.crypto = crypto
    
    def add_cred(self, platform, username, password, mfa=None):
        if not self.crypto: return False, "No password set"
        if platform in self.vault and username in [c['username'] for c in self.vault[platform]]: 
            return False, "Username exists"
        encrypted_password = self.crypto.encrypt_aes(password)
        encrypted_secret = self.crypto.encrypt_aes(mfa) if mfa else None
        if platform not in self.vault: self.vault[platform] = []
        credential = {'username': username, 'password': encrypted_password}
        if encrypted_secret: credential['mfa'] = encrypted_secret
        self.vault[platform].append(credential)
        self._save()
        return True, f"Added {username}"
    
    def edit_cred(self, platform, username, new_password=None, new_mfa=None):
        if not self.crypto: return False, "No password set"
        if platform not in self.vault: return False, "Platform not found"
        for cred in self.vault[platform]:
            if cred['username'] == username:
                if new_password: cred['password'] = self.crypto.encrypt_aes(new_password)
                if new_mfa is not None:
                    if new_mfa: cred['mfa'] = self.crypto.encrypt_aes(new_mfa)
                    elif 'mfa' in cred: del cred['mfa']
                self._save()
                return True, f"Updated {username}"
        return False, "Username not found"
    
    def del_cred(self, platform, username):
        if not self.crypto: return False, "No password set"
        if platform not in self.vault: return False, "Platform not found"
        for i, cred in enumerate(self.vault[platform]):
            if cred['username'] == username:
                self.vault[platform].pop(i)
                if not self.vault[platform]: del self.vault[platform]
                self._save()
                return True, f"Deleted {username}"
        return False, "Username not found"
    
    def get_platforms(self):
        return sorted(self.vault.keys())
    
    def get_credentials_for_platform(self, platform):
        if platform not in self.vault or not self.crypto: return []
        result = []
        for cred in self.vault[platform]:
            try:
                pwd = self.crypto.decrypt_aes(cred['password'])
                mfa = self.crypto.decrypt_aes(cred.get('mfa')) if cred.get('mfa') else None
                result.append({'username': cred['username'], 'password': pwd, 'mfa': mfa})
            except: pass
        return result
    
    def save(self):
        try:
            save_vault(self.vault)
            return True, "Saved"
        except Exception as e: 
            return False, str(e)
