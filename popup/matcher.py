import re
import win32gui
from credentials import load_vault

def get_window_title():
    hwnd = win32gui.GetForegroundWindow()
    return win32gui.GetWindowText(hwnd)

def get_matching_services():
    title = get_window_title().lower()
    parts = [p.strip() for p in re.split(r" - | \| | • | · ", title)]
    vault = load_vault()
    matches = {}

    for service, accounts in vault.items():
        service_l = service.lower()

        for part in parts:
            if service_l in part or part in service_l:
                matches[service] = accounts
                break
    return matches

def get_matching_accounts():
    matches = get_matching_services()
    accounts = []
    
    for service, service_accounts in matches.items():
        for account in service_accounts:
            accounts.append({
                "service": service,
                "username": account.get("username", ""),
                "password": account.get("password", ""),
                "mfa": account.get("mfa", "")
            })
    return accounts
