import json
import os
from classes import Crypto
from pathlib import Path

CREDENTIALS_FILE = "credentials.json"

class CredentialManager:
    def __init__(self):
        self.crypto = None
        self.credentials = self._load_credentials()
    
    def setup_master_password(self):
        master_password = input("Enter master password: ").strip()
        if not master_password:
            print("Error: Master password cannot be empty")
            return False
        
        self.crypto = Crypto(master_password)
        return True
    
    def _load_credentials(self):
        if os.path.exists(CREDENTIALS_FILE):
            try:
                with open(CREDENTIALS_FILE, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading credentials: {e}")
                return {}
        return {}
    
    def _save_credentials(self):
        try:
            with open(CREDENTIALS_FILE, 'w') as f:
                json.dump(self.credentials, f, indent=4)
            print("Credentials saved successfully")
        except Exception as e:
            print(f"Error saving credentials: {e}")
    
    def add_credential(self, platform, username, password, mfa=None):
        if not self.crypto:
            print("Error: Master password not set up")
            return False
        
        if platform in self.credentials:
            if username in [cred['username'] for cred in self.credentials[platform]]:
                print(f"Error: Username '{username}' already exists for {platform}")
                return False
        
        encrypted_password = self.crypto.encrypt_aes(password)
        encrypted_secret = self.crypto.encrypt_aes(mfa) if mfa else None
        
        if platform not in self.credentials:
            self.credentials[platform] = []
        
        credential = {
            'username': username,
            'password': encrypted_password
        }
        
        if encrypted_secret:
            credential['mfa'] = encrypted_secret
        
        self.credentials[platform].append(credential)
        
        self._save_credentials()
        print(f"Credential added for {platform} - {username}")
        return True
    
    def view_credentials(self, platform=None):
        if not self.crypto:
            print("Error: Master password not set up")
            return
        
        if platform:
            if platform not in self.credentials:
                print(f"No credentials found for {platform}")
                return
            
            for cred in self.credentials[platform]:
                decrypted_password = self.crypto.decrypt_aes(cred['password'])
                decrypted_secret = self.crypto.decrypt_aes(cred.get('mfa')) if cred.get('mfa') else None
                print(f"Platform: {platform}")
                print(f"  Username: {cred['username']}")
                print(f"  Password: {decrypted_password}")
                if decrypted_secret:
                    print(f"  Secret Code: {decrypted_secret}")
                print()
        else:
            for plat, creds in self.credentials.items():
                print(f"\n{plat}:")
                for cred in creds:
                    print(f"  - {cred['username']}")

def main():
    manager = CredentialManager()
    
    if not manager.setup_master_password():
        return
    
    while True:
        print("\n=== Credential Manager ===")
        print("1. Add credential")
        print("2. View all credentials")
        print("3. View credentials for platform")
        print("4. Exit")
        
        choice = input("Select option: ").strip()
        
        if choice == "1":
            platform = input("Enter platform name: ").strip()
            username = input("Enter username: ").strip()
            password = input("Enter password: ").strip()
            mfa = input("Enter secret code (optional, press Enter to skip): ").strip()
            
            if not platform or not username or not password:
                print("Error: Platform, username, and password are required")
                continue
            
            manager.add_credential(platform, username, password, mfa or None)
        
        elif choice == "2":
            manager.view_credentials()
        
        elif choice == "3":
            platform = input("Enter platform name: ").strip()
            manager.view_credentials(platform)
        
        elif choice == "4":
            print("Exiting...")
            break
        
        else:
            print("Invalid option")

if __name__ == "__main__":
    main()