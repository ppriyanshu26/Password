import tkinter as tk
import pyautogui
import keyboard
import threading
import win32gui
import win32process
import ctypes
import ctypes.wintypes
import json

FILE = "credentials.json"
current_popup = None

def type_username(u):
    keyboard.write(u)

def type_password(p):
    keyboard.write(p)

def type_both(u, p):
    keyboard.write(u)
    keyboard.press_and_release('tab')
    keyboard.write(p)

def type_totp(t):
    keyboard.write(t)

def show_submenu(parent, x, y, username, password, totp):
    menu = tk.Toplevel()
    menu.overrideredirect(True)
    menu.attributes("-topmost", True)
    menu.attributes("-alpha", 0.92)
    menu.configure(bg="#111")

    menu.geometry(f"+{x}+{y}")

    def close():
        try: menu.destroy()
        except: pass

    btn = lambda text, cmd: tk.Button(
        menu, text=text, bg="#222", fg="white",
        activebackground="#333",
        activeforeground="white",
        bd=0, padx=12, pady=4,
        command=lambda: (cmd(), close())
    ).pack(fill="x")

    btn("Type Username", lambda: type_username(username))
    btn("Type Password", lambda: type_password(password))
    btn("Type Both", lambda: type_both(username, password))
    if totp:
        btn("Type TOTP", lambda: type_totp(totp))

    tk.Button(menu, text="Close", bg="#222", fg="white",
              command=close, bd=0).pack(fill="x")

    return menu

def is_text_input_focused():
    hwnd = win32gui.GetForegroundWindow()
    tid, pid = win32process.GetWindowThreadProcessId(hwnd)
    class GUITHREADINFO(ctypes.Structure):
        _fields_ = [("cbSize", ctypes.c_uint), ("flags", ctypes.c_uint), ("hwndActive", ctypes.c_void_p), ("hwndFocus", ctypes.c_void_p), ("hwndCapture", ctypes.c_void_p), ("hwndMenuOwner", ctypes.c_void_p), ("hwndMoveSize", ctypes.c_void_p), ("hwndCaret", ctypes.c_void_p),("rcCaret", ctypes.wintypes.RECT)]

    gui = GUITHREADINFO()
    gui.cbSize = ctypes.sizeof(gui)

    ctypes.windll.user32.GetGUIThreadInfo(tid, ctypes.byref(gui))
    focus = gui.hwndFocus
    if not focus:
        return False
    class_name = win32gui.GetClassName(focus)
    editable_classes = {"Edit", "RichEdit20A", "RichEdit20W", "Chrome_WidgetWin_1", "MozillaWindowClass", "TextBox", "CabinetWClass"}
    return class_name in editable_classes

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
                results.append((username, lambda u=username: print(f"Selected: {u}")))
    return results

def show_menu():
    global current_popup
    if current_popup is not None:
        try: current_popup.destroy()
        except: pass
        current_popup = None

    x, y = pyautogui.position()

    win = tk.Toplevel()
    win.overrideredirect(True)
    win.attributes("-topmost", True)
    win.attributes("-alpha", 0.85)          # GLASS EFFECT HERE
    win.configure(bg="#1a1a1a")
    win.geometry(f"+{x+12}+{y+12}")

    current_popup = win

    frame = tk.Frame(win, bg="#1a1a1a", padx=10, pady=10)
    frame.pack()

    tk.Label(frame, text="Accounts", fg="white",
             bg="#1a1a1a", font=("Segoe UI", 11, "bold")
             ).pack(anchor="w", pady=(0,8))

    accounts = get_usernames()

    if not accounts:
        tk.Label(frame, text="No accounts found", fg="#ff4444",
                 bg="#1a1a1a", font=("Segoe UI", 10, "italic")
                 ).pack(pady=6)
    else:
        creds = load_creds()
        window_title = get_window().lower()
        first_name = window_title.split(" - ")[0].strip()

        selected_service = None
        for service in creds:
            if service.lower() in first_name: 
                selected_service = creds[service]
                break

        for a in selected_service:
            username = a["username"]
            password = a.get("password", "")
            totp = a.get("totp", "")

            row = tk.Frame(frame, bg="#1a1a1a")
            row.pack(fill="x", pady=3)

            tk.Label(row, text=username, fg="white", bg="#1a1a1a",
                     font=("Segoe UI", 10)).pack(side="left")

            # ⋮ three-dot menu
            def make_menu(u=username, p=password, t=totp):
                mx = win.winfo_x() + 160
                my = win.winfo_y() + row.winfo_y() + 25
                show_submenu(win, mx, my, u, p, t)

            tk.Button(
                row,
                text="⋮",
                fg="white", bg="#1a1a1a",
                activebackground="#333",
                bd=0,
                font=("Segoe UI", 14),
                command=make_menu
            ).pack(side="right")

    tk.Button(frame, text="Close", width=20,
              command=win.destroy,
              bg="#222", fg="white", bd=0
              ).pack(pady=6)

def hotkeys():
    while True:
        keyboard.wait("ctrl+shift+l")
        if is_text_input_focused():
            show_menu()
        else:
            pass

threading.Thread(target=hotkeys, daemon=True).start()
root = tk.Tk()
root.withdraw()
root.mainloop()
