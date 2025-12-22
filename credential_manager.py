import json
import os
from classes import Crypto
from config import VAULT_FILE

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
        if os.path.exists(VAULT_FILE):
            try:
                with open(VAULT_FILE, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading credentials: {e}")
                return {}
        return {}
    
    def _save_credentials(self):
        try:
            with open(VAULT_FILE, 'w') as f:
                json.dump(self.credentials, f, indent=4)
            print("Credentials saved successfully")
        except Exception as e:
            print(f"Error saving credentials: {e}")
    
    def add_credential(self, platform, username, password, secret_code=None):
        """Add a new credential"""
        if not self.crypto:
            print("Error: Master password not set up")
            return False
        
        if platform in self.credentials:
            if username in [cred['username'] for cred in self.credentials[platform]]:
                print(f"Error: Username '{username}' already exists for {platform}")
                return False
        
        encrypted_password = self.crypto.encrypt(password)
        encrypted_secret = self.crypto.encrypt(secret_code) if secret_code else None
        
        if platform not in self.credentials:
            self.credentials[platform] = []
        
        self.credentials[platform].append({
            'username': username,
            'password': encrypted_password,
            'secret_code': encrypted_secret
        })
        
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
                decrypted_password = self.crypto.decrypt(cred['password'])
                decrypted_secret = self.crypto.decrypt(cred['secret_code']) if cred['secret_code'] else None
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
            secret_code = input("Enter secret code (optional, press Enter to skip): ").strip()
            
            if not platform or not username or not password:
                print("Error: Platform, username, and password are required")
                continue
            
            manager.add_credential(platform, username, password, secret_code or None)
        
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