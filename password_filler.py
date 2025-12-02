import tkinter as tk
import pyautogui
import threading
import keyboard
from functions import get_matching_accounts, type_username, type_password, type_both, type_totp
from tools import Btn
from popup import close_popup, set_popup, bind_popup_events
from crypto import Crypto

def show_menu():
    close_popup()
    x, y = pyautogui.position()
    win = tk.Toplevel()
    set_popup(win)
    win.overrideredirect(True)
    win.attributes("-topmost", True)
    win.attributes("-alpha", 0.90)
    win.configure(bg="#1a1a1a")
    win.geometry(f"+{x+12}+{y+12}")

    bind_popup_events(win)
    frame = tk.Frame(win, bg="#1a1a1a", padx=10, pady=10)
    frame.pack()
    tk.Label(frame, text="Accounts", fg="white", bg="#1a1a1a", font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0, 8))

    accounts = get_matching_accounts()
    if not accounts:
        tk.Label(frame, text="No accounts found", fg="#ff4444", bg="#1a1a1a", font=("Segoe UI", 10, "italic")).pack(pady=6)
    else:
        for acc in accounts:
            username = acc["username"]
            password = acc.get("password", "")
            totp = acc.get("secretco", "")

            row = tk.Frame(frame, bg="#1a1a1a")
            row.pack(fill="x", pady=4)

            tk.Label(row, text=username, fg="white", bg="#1a1a1a", font=("Segoe UI", 10)).pack(side="left", padx=(0, 10))

            icons_frame = tk.Frame(row, bg="#1a1a1a")
            icons_frame.pack(side="right")

            icon_style = {"bg": "#1a1a1a", "fg": "#888", "activebackground": "#333", "activeforeground": "white", "bd": 0, "font": ("Segoe UI", 11), "cursor": "hand2", "width": 2}

            btn_user = tk.Button(icons_frame, text="👤", command=lambda u=username: type_username(u, close_popup), **icon_style)
            btn_user.pack(side="left", padx=1)
            Btn(btn_user, "Type Username")

            btn_pass = tk.Button(icons_frame, text="🔑", command=lambda p=password: type_password(p, close_popup), **icon_style)
            btn_pass.pack(side="left", padx=1)
            Btn(btn_pass, "Type Password")

            btn_both = tk.Button(icons_frame, text="⏩", command=lambda u=username, p=password: type_both(u, p, close_popup), **icon_style)
            btn_both.pack(side="left", padx=1)
            Btn(btn_both, "Type Both")

            if totp:
                btn_totp = tk.Button(icons_frame, text="🔢", command=lambda t=totp: type_totp(t, close_popup), **icon_style)
                btn_totp.pack(side="left", padx=1)
                Btn(btn_totp, "Type TOTP")

    tk.Button(frame, text="Close", width=20, command=close_popup, bg="#222", fg="white", activebackground="#333", activeforeground="white", bd=0).pack(pady=(8, 0))

def hotkeys():
    while True:
        keyboard.wait("ctrl+shift+l")
        show_menu()

threading.Thread(target=hotkeys, daemon=True).start()

root = tk.Tk()
root.withdraw()
root.mainloop()