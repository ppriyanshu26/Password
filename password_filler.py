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
        try:
            current_popup.destroy()
        except:
            pass
        current_popup = None
    x, y = pyautogui.position()

    win = tk.Toplevel()
    win.overrideredirect(True)
    win.attributes("-topmost", True)
    win.geometry(f"+{x+10}+{y+10}")
    current_popup = win

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
        if is_text_input_focused():
            show_menu()
        else:
            pass

threading.Thread(target=hotkeys, daemon=True).start()
root = tk.Tk()
root.withdraw()
root.mainloop()
