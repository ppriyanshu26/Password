import tkinter as tk
import pyautogui
import threading
import keyboard
import uiautomation as auto
from functions import get_matching_accounts, type_username, type_password, type_both, type_totp
from tools import Btn
from popup import close_popup, set_popup, bind_popup_events
from crypto import Crypto

TRIGGER_KEYWORDS = {"code", "mfa", "email", "password", "username", "phone", "verification", "authenticator", "authenticate", "number", "user name"}

def show_menu():
    element = auto.GetFocusedControl()
    name_words = set(element.Name.lower().split())
    if not name_words & TRIGGER_KEYWORDS:
        return
    
    accounts = get_matching_accounts()
    
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
    
    if not accounts:
        tk.Label(frame, text="No accounts found", fg="#ff4444", bg="#1a1a1a", font=("Segoe UI", 10, "italic")).pack(pady=6)
        tk.Button(frame, text="Close", width=20, command=close_popup, bg="#222", fg="white", activebackground="#333", activeforeground="white", bd=0).pack(pady=(8, 0))
        return
    
    tk.Label(frame, text="Enter Key:", fg="white", bg="#1a1a1a", font=("Segoe UI", 10)).pack(anchor="w")
    key_entry = tk.Entry(frame, show="*", bg="#333", fg="white", insertbackground="white", bd=0, font=("Segoe UI", 10))
    key_entry.pack(fill="x", pady=(4, 8))
    key_entry.focus_set()
    
    accounts_frame = tk.Frame(frame, bg="#1a1a1a")
    
    def show_accounts(event=None):
        key = key_entry.get()
        if not key:
            return
        
        crypto = Crypto(key)
        
        for widget in accounts_frame.winfo_children():
            widget.destroy()
        
        tk.Label(accounts_frame, text="Accounts", fg="white", bg="#1a1a1a", font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0, 8))
        
        for acc in accounts:
            username = acc["username"]
            password = crypto.decrypt_aes(acc.get("password", "")) or ""
            totp = crypto.decrypt_aes(acc.get("secretco", "")) if acc.get("secretco") else ""

            row = tk.Frame(accounts_frame, bg="#1a1a1a")
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
        
        accounts_frame.pack(fill="x")
        key_entry.config(state="disabled")
    
    key_entry.bind("<Return>", show_accounts)
    
    tk.Button(frame, text="Unlock", width=20, command=show_accounts, bg="#444", fg="white", activebackground="#555", activeforeground="white", bd=0).pack(pady=(4, 0))
    tk.Button(frame, text="Close", width=20, command=close_popup, bg="#222", fg="white", activebackground="#333", activeforeground="white", bd=0).pack(pady=(8, 0))

def hotkeys():
    with auto.UIAutomationInitializerInThread():
        while True:
            keyboard.wait("ctrl+shift+l")
            show_menu()

threading.Thread(target=hotkeys, daemon=True).start()

root = tk.Tk()
root.withdraw()
root.mainloop()