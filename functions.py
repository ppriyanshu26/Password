import json
import os
import re
import win32gui
import win32process
import psutil

FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "credentials.json")

def load_creds():
    if os.path.exists(FILE):
        with open(FILE, 'r') as f:
            return json.load(f)
    return {}

def save_creds(creds):
    with open(FILE, 'w') as f:
        json.dump(creds, f, indent=4)

def get_active_window_name():
    try:
        hwnd = win32gui.GetForegroundWindow()
        window_title = win32gui.GetWindowText(hwnd)
        
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        try:
            process = psutil.Process(pid)
            process_name = process.name().lower().replace('.exe', '')
            return process_name, window_title
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return window_title.lower(), window_title
    except Exception:
        return "unknown", "Unknown"

def extract_words(text):
    text = re.sub(r'[_\-./\\|]', ' ', text)
    text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)
    words = re.findall(r'[a-zA-Z0-9]+', text.lower())
    return words

def find_matching_credentials(window_title, process_name, credentials):
    title_words = extract_words(window_title)
    process_words = extract_words(process_name)
    all_words = set(title_words + process_words)
    
    matches = {}
    
    for app_key, creds in credentials.items():
        app_words = extract_words(app_key)
        for word in all_words:
            if len(word) >= 3: 
                for app_word in app_words:
                    if word in app_word or app_word in word:
                        matches[app_key] = creds
                        break
                if app_key in matches:
                    break
    return matches

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