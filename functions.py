import json
import pyotp
import time
import os

FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "credentials.json")
def generate_totp(secret):
    totp = pyotp.TOTP(secret)
    code = totp.now()
    time_left = 30 - int(time.time())%30
    return code, time_left
    
def load_creds():
    with open(FILE, 'r') as f:
        return json.load(f)
    return {}

def save_creds(creds):
    sorted_creds = dict(sorted(creds.items(), key=lambda x: x[0].lower()))
    with open(FILE, 'w') as f:
        json.dump(sorted_creds, f, indent=4)

def add_credential(app, username, password, secretco, crypto):
    creds = load_creds()
    new_cred = {
        "username": username,
        "password": crypto.encrypt_aes256(password)
    }
    if secretco:
        new_cred["secretco"] = crypto.encrypt_aes256(secretco)
    app = app.strip().lower()
    if app in creds:
        creds[app].append(new_cred)
    else:
        creds[app] = [new_cred]
    save_creds(creds)
    return True, f"Credential added for '{app}'!"

def delete_credential(app, username):
    creds = load_creds()
    original_count = len(creds[app])
    creds[app] = [c for c in creds[app] if c['username'] != username]
    if len(creds[app]) == original_count:
        return False, "Credential not found!"
    if not creds[app]:
        del creds[app]
    save_creds(creds)
    return True, f"Credential deleted for '{app}'!"