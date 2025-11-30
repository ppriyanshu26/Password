import json
import os
import time
import tkinter as tk
from tkinter import ttk, messagebox
import keyboard
import re

import win32gui  # type: ignore
import win32process  # type: ignore
import win32con  # type: ignore
import win32api  # type: ignore
import psutil

from classes import Totp

FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "credentials.json")
HOTKEY = "win+alt+z"

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

class PasswordFillerGUI:
    def __init__(self):
        self.root = None
        self.credentials = load_creds()
        self.last_app_name = ""
        self.last_window_title = ""
        
    def create_window(self):
        if self.root is not None:
            try:
                self.root.destroy()
            except:
                pass
        
        self.root = tk.Tk()
        self.root.title("Password Filler")
        self.root.geometry("400x350")
        self.root.attributes('-topmost', True)
        self.root.configure(bg='#2b2b2b')
        
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - 200
        y = (self.root.winfo_screenheight() // 2) - 175
        self.root.geometry(f"400x350+{x}+{y}")
        
        # Force window to get focus using Windows API
        self.root.lift()
        self.root.attributes('-topmost', True)
        self.root.after(10, self._force_focus)
        
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TFrame', background='#2b2b2b')
        style.configure('TLabel', background='#2b2b2b', foreground='white', font=('Segoe UI', 10))
        style.configure('Title.TLabel', font=('Segoe UI', 12, 'bold'))
        style.configure('TButton', font=('Segoe UI', 9))
        
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        app_name, window_title = get_active_window_name()
        self.last_app_name = app_name
        self.last_window_title = window_title
        
        ttk.Label(main_frame, text="Password Filler", style='Title.TLabel').pack(pady=(0, 10))
        
        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.cred_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, 
                                        bg='#3c3c3c', fg='white', 
                                        selectbackground='#0078d4',
                                        font=('Consolas', 10))
        self.cred_listbox.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.cred_listbox.yview)
        
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(btn_frame, text="Fill Creds", command=self.fill_creds).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Fill TOTP", command=self.fill_totp).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Search", command=self.show_all_creds).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Close", command=self.close_window).pack(side=tk.RIGHT, padx=2)
        
        self.root.bind('<Escape>', lambda e: self.close_window())
        self.root.bind('<Return>', lambda e: self.fill_creds())
        
        self.load_matching_creds()
        
        self.root.mainloop()
    
    def load_matching_creds(self):
        self.cred_listbox.delete(0, tk.END)
        self.matched_creds = []
        
        matches = find_matching_credentials(
            self.last_window_title, 
            self.last_app_name, 
            self.credentials
        )
        
        for app, creds in matches.items():
            for cred in creds:
                self.matched_creds.append((app, cred))
                display = f"[{app}] {cred['username']}"
                self.cred_listbox.insert(tk.END, display)
        
        if not self.matched_creds:
            for app, creds in self.credentials.items():
                for cred in creds:
                    self.matched_creds.append((app, cred))
                    display = f"[{app}] {cred['username']}"
                    self.cred_listbox.insert(tk.END, display)
        
        if self.matched_creds:
            self.cred_listbox.selection_set(0)
    
    def get_selected_cred(self):
        selection = self.cred_listbox.curselection()
        if selection and self.matched_creds:
            idx = selection[0]
            if idx < len(self.matched_creds):
                return self.matched_creds[idx]
        return None
    
    def fill_creds(self):
        cred = self.get_selected_cred()
        if cred:
            self.close_window()
            time.sleep(0.5)
            keyboard.write(cred[1]['username'])
            keyboard.press_and_release('tab')
            time.sleep(0.1)
            keyboard.write(cred[1]['password'])
    
    def fill_totp(self):
        cred = self.get_selected_cred()
        if cred:
            secret = cred[1].get('secretco')
            if secret:
                code, _ = Totp(secret).generate_totp()
                self.close_window()
                time.sleep(0.5)
                keyboard.write(code)
            else:
                messagebox.showwarning("No TOTP", "No TOTP assigned for this credential!")
    
    def show_all_creds(self):
        self.cred_listbox.delete(0, tk.END)
        self.matched_creds = []
        
        for app, creds in self.credentials.items():
            for cred in creds:
                self.matched_creds.append((app, cred))
                display = f"[{app}] {cred['username']}"
                self.cred_listbox.insert(tk.END, display)
        
        if self.matched_creds:
            self.cred_listbox.selection_set(0)
    
    def close_window(self):
        if self.root:
            self.root.destroy()
            self.root = None
    
    def _force_focus(self):
        """Force the window to get focus using Windows API"""
        try:
            hwnd = win32gui.FindWindow(None, "Password Filler")
            if hwnd:
                # Simulate pressing Alt to allow SetForegroundWindow to work
                win32api.keybd_event(win32con.VK_MENU, 0, 0, 0)
                win32api.keybd_event(win32con.VK_MENU, 0, win32con.KEYEVENTF_KEYUP, 0)
                
                win32gui.SetForegroundWindow(hwnd)
                win32gui.SetFocus(hwnd)
            
            self.root.focus_force()
            self.cred_listbox.focus_set()
        except Exception:
            pass

print(f"Password Filler Started!")
print(f"Press {HOTKEY.upper()} to open the password filler")
print("Press Ctrl+C in this console to exit")

app = PasswordFillerGUI()

keyboard.add_hotkey(HOTKEY, app.create_window)

try:
    keyboard.wait()
except KeyboardInterrupt:
    print("\nPassword Filler stopped.")
