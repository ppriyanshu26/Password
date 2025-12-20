import json
import keyboard
import win32gui
import re

FILE = "credentials.json"

def load_creds():
    with open(FILE, "r") as f:
        return json.load(f)

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
