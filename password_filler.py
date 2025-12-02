import tkinter as tk
import pyautogui
import keyboard
import threading
import win32gui
import json

FILE = "credentials.json"

def load_creds():
    with open(FILE, 'r') as f:
        return json.load(f)

def get_window():
    hwnd = win32gui.GetForegroundWindow()
    return win32gui.GetWindowText(hwnd)

def get_usernames():
    window_title = get_window().lower()
    first_name = window_title.split(" - ")[0].strip()
    data = load_creds()

    results = []
    for service, accounts in data.items():
        if service.lower() in first_name or first_name in service.lower():
            for account in accounts:
                username = account["username"]
                results.append(
                    (username, lambda u=username: print(f"Selected: {u}"))
                )
    return results

def show_menu():
    x, y = pyautogui.position()

    win = tk.Toplevel()
    win.overrideredirect(True)
    win.attributes("-topmost", True)
    win.geometry(f"+{x+10}+{y+10}")

    frame = tk.Frame(win, bg="#1e1e1e", padx=10, pady=10)
    frame.pack()

    tk.Label(frame, text="Menu", fg="white", bg="#1e1e1e", font=("Arial", 12, "bold")).pack(anchor="w", pady=(0, 10))

    user_options = get_usernames()

    if not user_options:
        tk.Label(frame, text="No accounts found", fg="red", bg="#1e1e1e", font=("Arial", 10, "italic")).pack(pady=5)
    else:
        for label, func in user_options:
            tk.Button(frame, text=label, width=20, command=lambda f=func: (f(), win.destroy())).pack(pady=3)

    tk.Button(frame, text="Close", width=20, command=win.destroy).pack(pady=8)

def hotkeys():
    while True:
        keyboard.wait("ctrl+shift+l")
        show_menu()

threading.Thread(target=hotkeys, daemon=True).start()
root = tk.Tk()
root.withdraw()
root.mainloop()
