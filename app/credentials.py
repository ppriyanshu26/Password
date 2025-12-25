import json
import os
import hashlib
import keyring
from config import SERVICE_NAME, USERNAME
from classes import Crypto

BASE_APP_DIR = os.getenv("APPDATA")
APP_FOLDER = os.path.join(BASE_APP_DIR, "Password-Manager")
os.makedirs(APP_FOLDER, exist_ok=True)
VAULT_FILE = os.path.join(APP_FOLDER, "credentials.json")

def hash_master_key(key):
    return hashlib.sha256(key.encode('utf-8')).hexdigest()

def save_master_key(key):
    hashed = hash_master_key(key)
    keyring.set_password(SERVICE_NAME, USERNAME, hashed)

def verify_master_key(key):
    stored_hash = keyring.get_password(SERVICE_NAME, USERNAME)
    if not stored_hash:
        return False
    return hash_master_key(key) == stored_hash

def master_key_exists():
    return keyring.get_password(SERVICE_NAME, USERNAME) is not None

def load_vault():
    if not os.path.exists(VAULT_FILE):
        return {}    
    with open(VAULT_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_vault(vault):
    with open(VAULT_FILE, "w", encoding="utf-8") as f:
        json.dump(vault, f, indent=2, ensure_ascii=False)
        f.flush()

def rotate_master_key(old_password, new_password):
    try:
        if not verify_master_key(old_password):
            return False, "Current master key is incorrect"
        vault = CredentialVault()
        old_crypto = Crypto(old_password)
        vault.set_crypto(old_crypto)
        vault.load()
        decrypted_vault = vault.decrypt_creds()
        
        save_master_key(new_password)
        new_crypto = Crypto(new_password)
        vault.set_crypto(new_crypto)
        reencrypted_vault = {}
        for platform, creds in decrypted_vault.items():
            reencrypted_vault[platform] = []
            for cred in creds:
                encrypted_pwd = new_crypto.encrypt_aes(cred['password'])
                encrypted_cred = {'username': cred['username'], 'password': encrypted_pwd}
                if cred.get('mfa'):
                    encrypted_cred['mfa'] = new_crypto.encrypt_aes(cred['mfa'])
                reencrypted_vault[platform].append(encrypted_cred)
        vault.vault = reencrypted_vault
        vault.save()
        return True, "Master key rotated successfully and all credentials re-encrypted"
    except Exception as e:
        return False, f"Error rotating master key: {str(e)}"

class CredentialVault:
    def __init__(self, crypto=None):
        self.crypto = crypto
        self.vault = load_vault()
    
    def set_crypto(self, crypto):
        self.crypto = crypto
    
    def load(self):
        self.vault = load_vault()
    
    def decrypt_creds(self):
        if not self.crypto:
            return {}
        decrypted_vault = {}
        for platform, creds in self.vault.items():
            decrypted_vault[platform] = []
            for cred in creds:
                try:
                    pwd = self.crypto.decrypt_aes(cred['password'])
                    mfa = self.crypto.decrypt_aes(cred.get('mfa')) if cred.get('mfa') else None
                    decrypted_cred = {'username': cred['username'], 'password': pwd}
                    if mfa:
                        decrypted_cred['mfa'] = mfa
                    decrypted_vault[platform].append(decrypted_cred)
                except:
                    pass
        return decrypted_vault
    
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
        self.save()
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
                self.save()
                return True, f"Updated {username}"
        return False, "Username not found"
    
    def del_cred(self, platform, username):
        if not self.crypto: return False, "No password set"
        if platform not in self.vault: return False, "Platform not found"
        for i, cred in enumerate(self.vault[platform]):
            if cred['username'] == username:
                self.vault[platform].pop(i)
                if not self.vault[platform]: del self.vault[platform]
                self.save()
                return True, f"Deleted {username}"
        return False, "Username not found"
    
    def get_platforms(self):
        return sorted(self.vault.keys())
    
    def get_creds_for_platform(self, platform):
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
