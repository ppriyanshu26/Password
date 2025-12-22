import tkinter as tk
import keyboard
import win32gui
import win32con
import win32process
import ctypes
import time
import pyperclip
from config import COLOR_BG_MEDIUM, COLOR_ACCENT
from classes import TooltipButton
from credentials import verify_master_key, master_key_exists, save_master_key

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

def create_account_frame(parent, account, idx, on_click_callback=None, popup_instance=None):
    frame = tk.Frame(parent, bg=COLOR_BG_MEDIUM, cursor="hand2")
    frame.account_data = account
    frame.index = idx
    content_frame = tk.Frame(frame, bg=COLOR_BG_MEDIUM)
    content_frame.pack(side="left", fill="both", expand=True)
    
    service_label = tk.Label(content_frame, text=f"🪪{account['service']}", font=("Segoe UI", 10, "bold"), bg=COLOR_BG_MEDIUM, fg=COLOR_ACCENT, anchor="w")
    service_label.pack(fill="x", padx=10, pady=(8, 2))
    
    username_label = tk.Label(content_frame, text=f"👤 {account['username']}", font=("Segoe UI", 9), bg=COLOR_BG_MEDIUM, fg="#ffffff", anchor="w")
    username_label.pack(fill="x", padx=10, pady=(0, 8))
    
    if on_click_callback:
        frame.bind("<Button-1>", lambda e, i=idx: on_click_callback(i))
        service_label.bind("<Button-1>", lambda e, i=idx: on_click_callback(i))
        username_label.bind("<Button-1>", lambda e, i=idx: on_click_callback(i))
    
    buttons_frame = tk.Frame(frame, bg=COLOR_BG_MEDIUM)
    buttons_frame.pack(side="right", padx=10, pady=8)
    
    btn1 = TooltipButton(buttons_frame, text="Button 1", emoji="📋", tooltip_text="Fill Credentials", command=lambda: button_click(1, account, popup_instance))
    btn1.pack(side="left", padx=2)
    
    btn2 = TooltipButton(buttons_frame, text="Button 2", emoji="🔑", tooltip_text="Copy Credentials", command=lambda: button_click(2, account, popup_instance))
    btn2.pack(side="left", padx=2)
    
    has_mfa = account.get("mfa") and account.get("mfa").strip()
    btn3 = TooltipButton(buttons_frame, text="Button 3", emoji="🔐", tooltip_text="2FA not configured" if not has_mfa else "Fill 2FA code", command=lambda: button_click(3, account, popup_instance) if has_mfa else None, state="disabled" if not has_mfa else "normal")
    btn3.pack(side="left", padx=2)
    
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

def verify_and_cache_master_key(key, cached_master_key_ref):
    if not key:
        return {"success": False, "error": "Please enter a master key"}
    if not master_key_exists():
        if len(key) < 4:
            return {"success": False, "error": "Key must be at least 4 characters"}
        save_master_key(key)
        return {"success": True, "is_setup": True, "key": key}
    if verify_master_key(key):
        return {"success": True, "is_setup": False, "key": key}
    else:
        return {"success": False, "error": "Invalid master key"}

def button_click(button_number, account, popup_instance):
    try:
        if popup_instance and popup_instance.root:
            if popup_instance.previous_focus_hwnd:
                try:
                    win32gui.SetForegroundWindow(popup_instance.previous_focus_hwnd)
                except:
                    pass
            popup_instance._close()
            time.sleep(0.1)
        if button_number == 1:
            keyboard.write(account['username'])
            keyboard.press_and_release("tab")
            keyboard.write(account['password'])
            keyboard.press_and_release("enter")
            print(f"[Password Manager] Credentials pasted for account: {account['service']} ({account['username']})")
        elif button_number == 2:
            credentials_text = f"{account['username']}\n{account['password']}"
            pyperclip.copy(credentials_text)
            print(f"[Password Manager] Credentials copied to clipboard for account: {account['service']}")
        elif button_number == 3:
            if account.get("mfa"):
                keyboard.write(account['mfa'])
                keyboard.press_and_release("enter")
                print(f"[Password Manager] 2FA Code: {account['mfa']}")
        print(f"[Password Manager] Button {button_number} pressed for account: {account['service']} ({account['username']})")
    except Exception as e:
        print(f"[Password Manager] Error handling button click: {e}")
