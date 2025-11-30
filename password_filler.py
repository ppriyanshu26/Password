import time
import tkinter as tk
from tkinter import ttk
import keyboard
import win32gui
import win32con
import win32api
from classes import Totp, Crypto
from functions import load_creds, get_active_window_name, find_matching_credentials

HOTKEY = "win+alt+z"

class PasswordFillerGUI:
    def __init__(self):
        self.root = None
        self.credentials = load_creds()
        self.crypto = None
        self.last_app_name = ""
        self.last_window_title = ""
        self.authenticated = False
        
    def create_window(self):
        if self.root is not None:
            try:
                self.root.destroy()
            except:
                pass
        
        app_name, window_title = get_active_window_name()
        self.last_app_name = app_name
        self.last_window_title = window_title
        
        self.root = tk.Tk()
        self.root.title("Password Filler")
        self.root.geometry("400x350")
        self.root.attributes('-topmost', True)
        self.root.configure(bg='#2b2b2b')
        
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth()//2)-200
        y = (self.root.winfo_screenheight()//2)-175
        self.root.geometry(f"400x350+{x}+{y}")
        
        self.root.lift()
        self.root.attributes('-topmost', True)
        self.root.after(10, self._force_focus)
        
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TFrame', background='#2b2b2b')
        style.configure('TLabel', background='#2b2b2b', foreground='white', font=('Segoe UI', 10))
        style.configure('Title.TLabel', font=('Segoe UI', 12, 'bold'))
        style.configure('TButton', font=('Segoe UI', 9))
        style.configure('Error.TLabel', background='#2b2b2b', foreground='#ff6b6b', font=('Segoe UI', 9))
        
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        self.root.bind('<Escape>', lambda e: self.close_window())
        
        if not self.authenticated:
            self.show_lock_screen()
        else:
            self.show_main_content()
        
        self.root.mainloop()
    
    def show_lock_screen(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        
        ttk.Label(self.main_frame, text="🔒 Password Filler", style='Title.TLabel').pack(pady=(30, 20))
        
        key_frame = ttk.Frame(self.main_frame)
        key_frame.pack(fill=tk.X, pady=10, padx=40)
        
        ttk.Label(key_frame, text="Encryption Key:").pack(anchor=tk.W)
        
        self.key_entry = tk.Entry(key_frame, show="•", font=('Segoe UI', 11), 
                                   bg='#3c3c3c', fg='white', insertbackground='white',
                                   relief='flat')
        self.key_entry.pack(fill=tk.X, pady=(5, 0), ipady=5)
        self.key_entry.focus_set()
        
        self.error_label = ttk.Label(self.main_frame, text="", style='Error.TLabel')
        self.error_label.pack(pady=(10, 0))
        ttk.Button(self.main_frame, text="Unlock", command=self.unlock).pack(pady=5)
        
        self.root.bind('<Return>', lambda e: self.unlock())
    
    def unlock(self):
        key = self.key_entry.get().strip()
        
        if len(key) < 8:
            self.error_label.config(text="Key must be at least 8 characters!")
            self.key_entry.delete(0, tk.END)
            self.key_entry.focus_set()
            return
        
        self.crypto = Crypto(key)
        self.authenticated = True
        self.show_main_content()
    
    def show_main_content(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        
        self.root.bind('<Return>', lambda e: self.edit_creds())
        
        ttk.Label(self.main_frame, text="Password Filler", style='Title.TLabel').pack(pady=(0, 10))
        
        list_frame = ttk.Frame(self.main_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.cred_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, 
                                        bg='#3c3c3c', fg='white', 
                                        selectbackground='#0078d4',
                                        font=('Consolas', 10))
        self.cred_listbox.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.cred_listbox.yview)
        
        btn_frame = ttk.Frame(self.main_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(btn_frame, text="Fill Creds", command=self.fill_creds).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Fill TOTP", command=self.fill_totp).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Edit", command=self.edit_creds).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Lock", command=self.lock).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Close", command=self.close_window).pack(side=tk.RIGHT, padx=2)
        
        self.message_label = ttk.Label(self.main_frame, text="", style='Error.TLabel')
        self.message_label.pack(pady=(5, 0))
        
        self.load_matching_creds()
        self.cred_listbox.focus_set()
    
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
            decrypted_password = self.crypto.decrypt_aes256(cred[1]['password'])
            keyboard.write(decrypted_password)
    
    def fill_totp(self):
        cred = self.get_selected_cred()
        if cred:
            secret = cred[1].get('secretco')
            if secret:
                decrypted_secret = self.crypto.decrypt_aes256(secret)
                code, _ = Totp(decrypted_secret).generate_totp()
                self.close_window()
                time.sleep(0.5)
                keyboard.write(code)
            else:
                self.show_inline_message("No TOTP assigned for this credential!", is_error=True)
    
    def edit_creds(self):
        self.cred_listbox.delete(0, tk.END)
        self.matched_creds = []
        
        for app, creds in self.credentials.items():
            for cred in creds:
                self.matched_creds.append((app, cred))
                display = f"[{app}] {cred['username']}"
                self.cred_listbox.insert(tk.END, display)
        
        if self.matched_creds:
            self.cred_listbox.selection_set(0)
    
    def lock(self):
        self.authenticated = False
        self.crypto = None
        self.show_lock_screen()
    
    def show_inline_message(self, message, is_error=False, duration=3000):
        if hasattr(self, 'message_label'):
            self.message_label.config(text=message)
            self.root.after(duration, lambda: self.message_label.config(text=""))
    
    def close_window(self):
        if self.root:
            self.root.destroy()
            self.root = None
    
    def _force_focus(self):
        try:
            hwnd = win32gui.FindWindow(None, "Password Filler")
            if hwnd:
                win32api.keybd_event(win32con.VK_MENU, 0, 0, 0)
                win32api.keybd_event(win32con.VK_MENU, 0, win32con.KEYEVENTF_KEYUP, 0)
                win32gui.SetForegroundWindow(hwnd)
                win32gui.SetFocus(hwnd)
            
            self.root.focus_force()
            self.cred_listbox.focus_set()
        except Exception:
            pass

if __name__ == "__main__":
    print("Password Filler - Started!")
    print(f"Press {HOTKEY.upper()} to open the password filler")
    print("Press Ctrl+C in this console to exit")
    
    app = PasswordFillerGUI()
    
    keyboard.add_hotkey(HOTKEY, app.create_window)
    
    try:
        keyboard.wait()
    except KeyboardInterrupt:
        print("\nPassword Filler stopped.")
