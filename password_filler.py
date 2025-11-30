import time
import tkinter as tk
from tkinter import ttk
import keyboard
import win32gui
import win32con
import win32api
from classes import Totp, Crypto
from functions import load_creds, get_active_window_name, find_matching_credentials, add_credential, delete_credential

class PasswordFillerGUI:
    def __init__(self):
        self.root = None
        self.credentials = load_creds()
        self.crypto = None
        self.last_app_name = ""
        self.last_window_title = ""
        
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
        self.root.title("Password Filler v1.0.0")
        self.root.resizable(False, False)
        self.root.attributes('-topmost', True)
        self.root.configure(bg='#2b2b2b')
        
        self.root.withdraw()
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth()//2)-225
        y = (self.root.winfo_screenheight()//2)-200
        self.root.geometry(f"450x400+{x}+{y}")
        self.root.deiconify()
        
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
        
        self.show_lock_screen()
        
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
        self.show_main_content()
    
    def show_main_content(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        
        self.root.bind('<Escape>', lambda e: self.close_window())
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
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        
        self.root.bind('<Escape>', lambda e: self.show_main_content())
        self.root.bind('<Return>', lambda e: self.show_add_form())
        
        ttk.Label(self.main_frame, text="Edit Credentials", style='Title.TLabel').pack(pady=(0, 10))
        
        list_frame = ttk.Frame(self.main_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.cred_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, 
                                        bg='#3c3c3c', fg='white', 
                                        selectbackground='#0078d4',
                                        font=('Consolas', 10))
        self.cred_listbox.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.cred_listbox.yview)
        
        self.cred_listbox.delete(0, tk.END)
        self.matched_creds = []
        
        for app, creds in self.credentials.items():
            for cred in creds:
                self.matched_creds.append((app, cred))
                display = f"[{app}] {cred['username']}"
                self.cred_listbox.insert(tk.END, display)
        
        if self.matched_creds:
            self.cred_listbox.selection_set(0)
        
        btn_frame = ttk.Frame(self.main_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(btn_frame, text="Add New", command=self.show_add_form).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Delete", command=self.confirm_delete).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Back", command=self.show_main_content).pack(side=tk.RIGHT, padx=2)
        
        self.message_label = ttk.Label(self.main_frame, text="", style='Error.TLabel')
        self.message_label.pack(pady=(5, 0))
    
    def show_add_form(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        
        self.root.bind('<Escape>', lambda e: self.edit_creds())
        self.root.bind('<Return>', lambda e: self.save_new_credential())
        
        ttk.Label(self.main_frame, text="Add Credential", style='Title.TLabel').pack(pady=(0, 10))
        
        form_frame = ttk.Frame(self.main_frame)
        form_frame.pack(fill=tk.X, pady=5, padx=20)
        
        ttk.Label(form_frame, text="App Name:").pack(anchor=tk.W)
        self.app_entry = tk.Entry(form_frame, font=('Segoe UI', 10), 
                                   bg='#3c3c3c', fg='white', insertbackground='white', relief='flat')
        self.app_entry.pack(fill=tk.X, pady=(2, 8), ipady=4)
        
        ttk.Label(form_frame, text="Username:").pack(anchor=tk.W)
        self.username_entry = tk.Entry(form_frame, font=('Segoe UI', 10), 
                                        bg='#3c3c3c', fg='white', insertbackground='white', relief='flat')
        self.username_entry.pack(fill=tk.X, pady=(2, 8), ipady=4)
        
        ttk.Label(form_frame, text="Password:").pack(anchor=tk.W)
        self.password_entry = tk.Entry(form_frame, show="•", font=('Segoe UI', 10), 
                                        bg='#3c3c3c', fg='white', insertbackground='white', relief='flat')
        self.password_entry.pack(fill=tk.X, pady=(2, 8), ipady=4)
        
        ttk.Label(form_frame, text="TOTP Secret (optional):").pack(anchor=tk.W)
        self.secret_entry = tk.Entry(form_frame, font=('Segoe UI', 10), 
                                      bg='#3c3c3c', fg='white', insertbackground='white', relief='flat')
        self.secret_entry.pack(fill=tk.X, pady=(2, 8), ipady=4)
        
        btn_frame = ttk.Frame(self.main_frame)
        btn_frame.pack(fill=tk.X, pady=10, padx=20)
        
        ttk.Button(btn_frame, text="Save", command=self.save_new_credential).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Cancel", command=self.edit_creds).pack(side=tk.LEFT, padx=2)
        
        self.message_label = ttk.Label(self.main_frame, text="", style='Error.TLabel')
        self.message_label.pack(pady=(5, 0))
        
        self.app_entry.focus_set()
    
    def save_new_credential(self):
        app = self.app_entry.get().strip()
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        secret = self.secret_entry.get().strip()
        
        if not app or not username or not password:
            self.show_inline_message("App, username and password are required!")
            return
        success, message = add_credential(app, username, password, secret, self.crypto)
        
        if success:
            self.credentials = load_creds()
            self.show_inline_message(message, is_error=False)
            self.root.after(1000, self.edit_creds)
        else:
            self.show_inline_message(message)
    
    def confirm_delete(self):
        cred = self.get_selected_cred()
        if not cred:
            self.show_inline_message("Please select a credential to delete!")
            return
        
        for widget in self.main_frame.winfo_children():
            widget.destroy()

        ttk.Label(self.main_frame, text="Confirm Delete", style='Title.TLabel').pack(pady=(30, 20))
        
        app, cred_data = cred
        ttk.Label(self.main_frame, text=f"Are you sure you want to delete:").pack(pady=5)
        ttk.Label(self.main_frame, text=f"[{app}] {cred_data['username']}", 
                  font=('Consolas', 11, 'bold')).pack(pady=10)
        
        btn_frame = ttk.Frame(self.main_frame)
        btn_frame.pack(pady=20)
        
        ttk.Button(btn_frame, text="Yes, Delete", 
                   command=lambda: self.delete_selected(app, cred_data['username'])).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="Cancel", command=self.edit_creds).pack(side=tk.LEFT, padx=10)
        
        self.message_label = ttk.Label(self.main_frame, text="", style='Error.TLabel')
        self.message_label.pack(pady=(5, 0))
    
    def delete_selected(self, app, username):
        success, message = delete_credential(app, username)
        
        if success:
            self.credentials = load_creds()
            self.show_inline_message(message, is_error=False)
            self.root.after(1000, self.edit_creds)
        else:
            self.show_inline_message(message)
    
    def show_inline_message(self, message, is_error=False, duration=3000):
        if hasattr(self, 'message_label'):
            self.message_label.config(text=message)
            self.root.after(duration, lambda: self.message_label.config(text=""))
    
    def close_window(self):
        if self.root:
            self.root.destroy()
            self.root = None
        self.crypto = None
    
    def _force_focus(self):
        try:
            hwnd = win32gui.FindWindow(None, "Password Filler")
            if hwnd:
                win32api.keybd_event(win32con.VK_MENU, 0, 0, 0)
                win32api.keybd_event(win32con.VK_MENU, 0, win32con.KEYEVENTF_KEYUP, 0)
                win32gui.SetForegroundWindow(hwnd)
                win32gui.SetFocus(hwnd)
            
            self.root.focus_force()
            
            if hasattr(self, 'key_entry'):
                self.key_entry.focus_set()
            elif hasattr(self, 'cred_listbox'):
                self.cred_listbox.focus_set()
        except Exception:
            pass

if __name__ == "__main__":
    
    app = PasswordFillerGUI()
    app.create_window()
