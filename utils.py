import tkinter as tk
import win32gui
import win32con
import win32process
import ctypes
from config import COLOR_BG_MEDIUM, COLOR_ACCENT

def force_foreground(root):
    try:
        root.update()
        hwnd = win32gui.GetParent(root.winfo_id())
        
        foreground = win32gui.GetForegroundWindow()
        foreground_thread, _ = win32process.GetWindowThreadProcessId(foreground)
        current_thread = ctypes.windll.kernel32.GetCurrentThreadId()
        
        ctypes.windll.user32.AttachThreadInput(foreground_thread, current_thread, True)
        
        win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
        win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0,
                              win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
        win32gui.SetForegroundWindow(hwnd)
        win32gui.BringWindowToTop(hwnd)
        
        ctypes.windll.user32.AttachThreadInput(foreground_thread, current_thread, False)
    except Exception as e:
        print(f"Focus error: {e}")

def create_account_frame(parent, account, idx, on_click_callback):
    frame = tk.Frame(parent, bg=COLOR_BG_MEDIUM, cursor="hand2")
    frame.account_data = account
    frame.index = idx
    
    service_label = tk.Label(
        frame,
        text=f"🪪{account['service']}",
        font=("Segoe UI", 10, "bold"),
        bg=COLOR_BG_MEDIUM,
        fg=COLOR_ACCENT,
        anchor="w"
    )
    service_label.pack(fill="x", padx=10, pady=(8, 2))
    
    username_label = tk.Label(
        frame,
        text=f"👤 {account['username']}",
        font=("Segoe UI", 9),
        bg=COLOR_BG_MEDIUM,
        fg="#ffffff",
        anchor="w"
    )
    username_label.pack(fill="x", padx=10, pady=(0, 8))
    
    frame.bind("<Button-1>", lambda e, i=idx: on_click_callback(i))
    service_label.bind("<Button-1>", lambda e, i=idx: on_click_callback(i))
    username_label.bind("<Button-1>", lambda e, i=idx: on_click_callback(i))
    
    return frame


def highlight_items(account_frames, index):
    for i, frame in enumerate(account_frames):
        if i == index:
            frame.configure(bg="#4a4a6a")
            for child in frame.winfo_children():
                child.configure(bg="#4a4a6a")
        else:
            frame.configure(bg=COLOR_BG_MEDIUM)
            for child in frame.winfo_children():
                child.configure(bg=COLOR_BG_MEDIUM)


def show_toast(message):
    print(f"[Password Manager] {message}")
