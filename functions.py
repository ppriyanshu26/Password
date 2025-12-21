import json
import keyboard
import win32gui
import re
from crypto import Crypto

FILE = "credentials.json"
MASTER_KEY_HASH_FILE = "masterkey.hash"

def load_creds():
    with open(FILE, "r") as f:
        return json.load(f)

def save_creds(data):
    with open(FILE, "w") as f:
        json.dump(data, f, indent=4)

def load_master_key_hash():
    try:
        with open(MASTER_KEY_HASH_FILE, "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        return None

def save_master_key_hash(key):
    crypto = Crypto(key)
    with open(MASTER_KEY_HASH_FILE, "w") as f:
        f.write(crypto.encrypt_aes("VALID_KEY_CHECK"))

def verify_master_key(key):
    stored = load_master_key_hash()
    if stored is None:
        return None
    return Crypto(key).decrypt_aes(stored) == "VALID_KEY_CHECK"

def get_platforms():
    return sorted(load_creds().keys())

def get_accounts_for_platform(platform):
    return load_creds().get(platform, [])

def add_credential(platform, username, password, secretco, master_key):
    data = load_creds()
    crypto = Crypto(master_key)
    
    new_acc = {"username": username, "password": crypto.encrypt_aes(password)}
    if secretco:
        new_acc["secretco"] = crypto.encrypt_aes(secretco)
    
    if platform not in data:
        data[platform] = []
    
    for acc in data[platform]:
        if acc["username"] == username:
            return False, "Username already exists for this platform"
    
    data[platform].append(new_acc)
    save_creds(data)
    return True, "Credential added successfully"

def delete_credential(platform, username):
    data = load_creds()
    if platform not in data:
        return False, "Platform not found"
    
    orig_len = len(data[platform])
    data[platform] = [a for a in data[platform] if a["username"] != username]
    
    if len(data[platform]) == orig_len:
        return False, "Username not found"
    
    if not data[platform]:
        del data[platform]
    
    save_creds(data)
    return True, "Credential deleted successfully"

def update_credential(platform, username, password, secretco, master_key):
    data = load_creds()
    crypto = Crypto(master_key)
    
    if platform not in data:
        return False, "Platform not found"
    
    for acc in data[platform]:
        if acc["username"] == username:
            if password:
                acc["password"] = crypto.encrypt_aes(password)
            if secretco:
                acc["secretco"] = crypto.encrypt_aes(secretco)
            elif "secretco" in acc and secretco == "":
                del acc["secretco"]
            save_creds(data)
            return True, "Credential updated successfully"
    
    return False, "Username not found"

def get_matching_accounts():
    title = get_window_title().lower()
    parts = [p.strip() for p in re.split(r" - | \| | • | · ", title)]
    data = load_creds()

    for service, accounts in data.items():
        for part in parts:
            if service.lower() in part or part in service.lower():
                return accounts
    return []

def type_username(u, close_callback):
    close_callback()
    keyboard.write(u)

def type_password(p, close_callback):
    close_callback()
    keyboard.write(p)

def type_both(u, p, close_callback):
    close_callback()
    keyboard.write(u)
    keyboard.press_and_release("tab")
    keyboard.write(p)
    keyboard.press_and_release("enter")

def type_totp(t, close_callback):
    close_callback()
    keyboard.write(t)
    keyboard.press_and_release("enter")

def get_window_title():
    hwnd = win32gui.GetForegroundWindow()
    return win32gui.GetWindowText(hwnd)
