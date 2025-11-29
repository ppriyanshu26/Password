import json
import os

FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "credentials.json")

def load_creds():
    if os.path.exists(FILE):
        with open(FILE, 'r') as f:
            return json.load(f)
    return {}

def save_creds(creds):
    with open(FILE, 'w') as f:
        json.dump(creds, f, indent=4)

def add_cred():
    print("\n=== Add New Credential ===\n")
    app = input("App Name: ").strip().lower()
    
    if not app:
        print("App name cannot be empty!")
        return
    username = input("Username: ").strip()
    
    if not username:
        print("Username cannot be empty!")
        return
    password = input("Password: ").strip()
    
    if not password:
        print("Password cannot be empty!")
        return
    creds = load_creds()
    new_cred = {"username": username, "password": password}
    
    if app in creds:
        creds[app].append(new_cred)
    else:
        creds[app] = [new_cred]
    save_creds(creds)
    print(f"\n✓ Credential added for '{app}'!")

def list_creds():
    creds = load_creds()
    
    if not creds:
        print("\nNo credentials stored.")
        return
    
    print("\n=== Stored Credentials ===\n")
    for app, creds_list in creds.items():
        print(f"[{app}]")
        for cred in creds_list:
            print(f"  - {cred['username']}")
    print()

while True:
    print("\n--- Credential Manager ---")
    print("1. Add credential")
    print("2. List credentials")
    print("3. Exit")
    choice = input("\nChoice: ").strip()
    
    if choice == "1":
        add_cred()
    elif choice == "2":
        list_creds()
    elif choice == "3":
        print("Bye!")
        break
    else:
        print("Invalid choice!")

