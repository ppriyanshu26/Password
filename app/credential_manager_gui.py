import tkinter as tk
from tkinter import ttk
import pyperclip
from classes import Crypto
from config import COLOR_BG_DARK, COLOR_BG_MEDIUM, COLOR_ACCENT, COLOR_TEXT_PRIMARY, COLOR_ERROR, APP_NAME, APP_VERSION
import credentials as cred
from utils import export_credentials_to_excel
import pyotp

class CredentialManager:
    def __init__(self):
        self.crypto = None; self.vault = cred.CredentialVault(); self.master_key = None
    
    def setup_master_password(self, password):
        if not password: return False
        if not cred.master_key_exists(): 
            cred.save_master_key(password)
            self.crypto = Crypto(password)
            self.master_key = password
            self.vault.set_crypto(self.crypto)
            self.vault.load()
            return True
        if cred.verify_master_key(password):
            self.crypto = Crypto(password)
            self.master_key = password
            self.vault.set_crypto(self.crypto)
            self.vault.load()
            return True
        return False
    
    def add_cred(self, platform, username, password, mfa=None):
        return self.vault.add_cred(platform, username, password, mfa)
    
    def edit_cred(self, platform, username, new_password=None, new_mfa=None):
        return self.vault.edit_cred(platform, username, new_password, new_mfa)
    
    def del_cred(self, platform, username):
        return self.vault.del_cred(platform, username)
    
    def get_platforms(self): 
        return self.vault.get_platforms()
    
    def get_creds_for_platform(self, platform):
        return self.vault.get_creds_for_platform(platform)

class CredentialManagerGUI:
    def __init__(self, root):
        self.root = root; self.root.title(APP_NAME+" "+APP_VERSION); self.root.geometry("650x350"); self.root.configure(bg=COLOR_BG_DARK); self.manager = CredentialManager(); self.current_platform = None; self.current_credential = None; self.detail_text = None; self.current_dialog = None; self.create_login_screen()
    
    def create_login_screen(self):
        for widget in self.root.winfo_children(): widget.destroy()
        frame = tk.Frame(self.root, bg=COLOR_BG_DARK)
        frame.pack(expand=True, fill="both", padx=20, pady=20)
        tk.Label(frame, text="🔐 Password Manager", font=("Segoe UI", 24, "bold"), bg=COLOR_BG_DARK, fg=COLOR_ACCENT).pack(pady=20)
        tk.Label(frame, text="Enter Master Password", font=("Segoe UI", 12), bg=COLOR_BG_DARK, fg=COLOR_TEXT_PRIMARY).pack(pady=10)
        password_var = tk.StringVar()
        password_entry = tk.Entry(frame, textvariable=password_var, show="•", font=("Segoe UI", 11), width=30)
        password_entry.pack(pady=10)
        password_entry.focus()
        error_label = tk.Label(frame, text="", font=("Segoe UI", 10), bg=COLOR_BG_DARK, fg=COLOR_ERROR)
        error_label.pack(pady=5)
        def login():
            if self.manager.setup_master_password(password_var.get()): 
                self.create_main_screen()
            else: 
                error_label.config(text="❌ Incorrect Password")
                password_entry.delete(0, tk.END)
                password_entry.focus()
        tk.Button(frame, text="Login", command=login, font=("Segoe UI", 11), bg=COLOR_ACCENT, fg=COLOR_BG_DARK, padx=20, pady=10, relief="flat").pack(pady=20)
        password_entry.bind("<Return>", lambda e: login())
    
    def create_main_screen(self):
        for widget in self.root.winfo_children(): widget.destroy()
        header = tk.Frame(self.root, bg=COLOR_BG_MEDIUM, height=50)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text="🔐 Password Manager", font=("Segoe UI", 16, "bold"), bg=COLOR_BG_MEDIUM, fg=COLOR_ACCENT).pack(side="left", padx=20, pady=10)
        tk.Button(header, text="🚪 Logout", command=self.on_logout, font=("Segoe UI", 10), bg=COLOR_ERROR, fg="white", relief="flat", padx=10, pady=5).pack(side="right", padx=20, pady=10)
        
        content = tk.Frame(self.root, bg=COLOR_BG_DARK)
        content.pack(fill="both", expand=False, padx=20, pady=20)
        
        sel_frame = tk.Frame(content, bg=COLOR_BG_DARK)
        sel_frame.pack(fill="x", pady=(0, 15))
        
        tk.Label(sel_frame, text="📋 Platform:", font=("Segoe UI", 11, "bold"), bg=COLOR_BG_DARK, fg=COLOR_ACCENT).pack(side="left", padx=(0, 10))
        self.plat_combo = ttk.Combobox(sel_frame, font=("Segoe UI", 10), state="readonly", width=20)
        self.plat_combo['values'] = sorted(self.manager.get_platforms())
        self.plat_combo.pack(side="left", padx=(0, 10))
        self.plat_combo.bind("<<ComboboxSelected>>", self.platform_change)
        tk.Button(sel_frame, text="➕", command=self.add_platform, font=("Segoe UI", 10), bg=COLOR_ACCENT, fg=COLOR_BG_DARK, relief="flat", padx=8, pady=3).pack(side="left", padx=(0, 20))
        tk.Button(sel_frame, text="➖", command=self.del_platform, font=("Segoe UI", 10), bg=COLOR_ERROR, fg="white", relief="flat", padx=8, pady=3).pack(side="left", padx=(0, 20))
        tk.Label(sel_frame, text="🔑 User:", font=("Segoe UI", 11, "bold"), bg=COLOR_BG_DARK, fg=COLOR_ACCENT).pack(side="left", padx=(0, 10))
        self.user_combo = ttk.Combobox(sel_frame, font=("Segoe UI", 10), state="readonly", width=20)
        self.user_combo.pack(side="left")
        self.user_combo.bind("<<ComboboxSelected>>", self.credential_change)
        
        detail_container = tk.Frame(content, bg=COLOR_BG_DARK)
        detail_container.pack(fill="both", expand=False, pady=(0, 15))
        detail_frame = tk.Frame(detail_container, bg=COLOR_BG_MEDIUM, relief="flat")
        detail_frame.pack(fill="both", expand=True, side="left", padx=(0, 10))
        
        self.detail_text = tk.Text(detail_frame, font=("Segoe UI", 10), bg=COLOR_BG_DARK, fg=COLOR_TEXT_PRIMARY, relief="flat", padx=15, pady=15, wrap="word", height=8, width=50)
        self.detail_text.pack(fill="both", expand=True, padx=1, pady=1)
        self.detail_text.config(state="disabled")
        
        self.copy_btn_frame = tk.Frame(detail_container, bg=COLOR_BG_DARK)
        self.copy_btn_frame.pack(side="left", fill="y", padx=10)
        self.copy_username_btn = tk.Button(self.copy_btn_frame, text="Copy Username", command=lambda: pyperclip.copy(self.current_credential['username']), font=("Segoe UI", 8), bg=COLOR_ACCENT, fg=COLOR_BG_DARK, relief="flat", padx=8, pady=10, state="disabled", width=10)
        self.copy_username_btn.pack(side="top", pady=5)
        self.copy_password_btn = tk.Button(self.copy_btn_frame, text="Copy Password", command=lambda: pyperclip.copy(self.current_credential['password']), font=("Segoe UI", 8), bg=COLOR_ACCENT, fg=COLOR_BG_DARK, relief="flat", padx=8, pady=10, state="disabled", width=10)
        self.copy_password_btn.pack(side="top", pady=5)
        self.copy_totp_btn = tk.Button(self.copy_btn_frame, text="Copy TOTP", command=self.copy_totp, font=("Segoe UI", 8), bg=COLOR_ACCENT, fg=COLOR_BG_DARK, relief="flat", padx=8, pady=10, state="disabled", width=10)
        self.copy_totp_btn.pack(side="top", pady=5)
        
        btn_frame = tk.Frame(content, bg=COLOR_BG_DARK)
        btn_frame.pack(fill="x")
        tk.Button(btn_frame, text="➕ Add", command=self.add_creds, font=("Segoe UI", 10), bg=COLOR_ACCENT, fg=COLOR_BG_DARK, relief="flat", padx=15, pady=8).pack(side="left", padx=5)
        tk.Button(btn_frame, text="✏️ Edit", command=self.edit_creds, font=("Segoe UI", 10), bg=COLOR_ACCENT, fg=COLOR_BG_DARK, relief="flat", padx=15, pady=8).pack(side="left", padx=5)
        tk.Button(btn_frame, text="🗑️ Delete", command=self.del_creds, font=("Segoe UI", 10), bg=COLOR_ERROR, fg="white", relief="flat", padx=15, pady=8).pack(side="left", padx=5)
        tk.Button(btn_frame, text="🔐 Change Master Key", command=self.update_key, font=("Segoe UI", 10), bg="#FFA500", fg="white", relief="flat", padx=15, pady=8).pack(side="left", padx=5)
        tk.Button(btn_frame, text="⬇️ Export", command=self.export_credentials, font=("Segoe UI", 10), bg="#4CAF50", fg="white", relief="flat", padx=15, pady=8).pack(side="left", padx=5)
    
    def platform_change(self, event):
        self.current_platform = self.plat_combo.get()
        sorted_users = sorted([c['username'] for c in self.manager.get_creds_for_platform(self.current_platform)])
        self.user_combo['values'] = sorted_users
        self.user_combo.set('')
        self.clear_details()
    
    def credential_change(self, event):
        if not self.current_platform: return
        username = self.user_combo.get()
        creds = self.manager.get_creds_for_platform(self.current_platform)
        for c in creds:
            if c['username'] == username:
                self.current_credential = c
                self.show_details()
                break

    def show_details(self):
        if not self.current_credential: return
        c = self.current_credential
        text = f"Username: {c['username']}\n\nPassword: {c['password']}\n"
        if c.get('mfa'):
            totp = pyotp.TOTP(c['mfa'])
            current_code = totp.now()
            text += f"\nMFA Secret Key: {c['mfa']}\n\nCurrent TOTP: {current_code}"
        else:
            text += "\nMFA: Not configured"
        self.detail_text.config(state="normal")
        self.detail_text.delete(1.0, "end")
        self.detail_text.insert(1.0, text)
        self.detail_text.config(state="disabled")
        self.copy_username_btn.config(state="normal")
        self.copy_password_btn.config(state="normal")
        self.copy_totp_btn.config(state="normal")

    def clear_details(self):
        self.detail_text.config(state="normal")
        self.detail_text.delete(1.0, "end")
        self.detail_text.config(state="disabled")
        self.copy_username_btn.config(state="disabled")
        self.copy_password_btn.config(state="disabled")
        self.copy_totp_btn.config(state="disabled")

    def copy_totp(self):
        if self.current_credential and self.current_credential.get('mfa'):
            totp = pyotp.TOTP(self.current_credential['mfa'])
            pyperclip.copy(totp.now())  
    
    def show_message(self, title, message, on_back=None):
        self.current_dialog = {"type": "message"}
        self.detail_text.config(state="normal")
        self.detail_text.delete(1.0, "end")
        msg = f"{title}\n\n{message}\n\n[ESC] Back"
        self.detail_text.insert(1.0, msg)
        self.detail_text.config(state="disabled")
        def back(e=None):
            if on_back: on_back()
            else: self.clear_details()
            self.current_dialog = None
        self.detail_text.bind("<Escape>", back)
        self.detail_text.focus()
    
    def show_confirmation(self, title, message, on_yes, on_no):
        self.current_dialog = {"type": "confirmation", "on_yes": on_yes, "on_no": on_no}
        self.detail_text.config(state="normal")
        self.detail_text.delete(1.0, "end")
        msg = f"{title}\n\n{message}\n\n[ENTER] Yes  [ESC] No"
        self.detail_text.insert(1.0, msg)
        self.detail_text.config(state="disabled")
        def submit(e=None):
            if self.current_dialog and self.current_dialog["type"] == "confirmation":
                on_yes()
                self.current_dialog = None
        def cancel(e=None):
            if self.current_dialog and self.current_dialog["type"] == "confirmation":
                on_no()
                self.current_dialog = None
        self.detail_text.bind("<Return>", submit)
        self.detail_text.bind("<Escape>", cancel)
        self.detail_text.focus()
    
    def show_input_dialog(self, title, fields, on_submit, on_cancel):
        self.current_dialog = {"type": "input", "fields": {}, "field_order": fields, "index": 0, "on_submit": on_submit, "on_cancel": on_cancel}
        for field in fields: self.current_dialog["fields"][field] = tk.StringVar()
        self.render_input_dialog(title)
    
    def render_input_dialog(self, title):
        if not self.current_dialog or self.current_dialog["type"] != "input": return
        self.detail_text.config(state="normal")
        self.detail_text.delete(1.0, "end")
        fields = self.current_dialog["field_order"]
        idx = self.current_dialog["index"]
        current_field = fields[idx]
        msg = f"{title}\n\n{current_field}:\n{self.current_dialog['fields'][current_field].get()}"
        msg += f"\n\n[ENTER] Next  [ESC] Cancel"
        if idx == len(fields) - 1: msg = msg.replace("[ENTER] Next", "[ENTER] Submit")
        self.detail_text.insert(1.0, msg)
        self.detail_text.config(state="disabled")
        
        fields_copy = fields
        dialog_fields = self.current_dialog["fields"]
        on_submit_cb = self.current_dialog["on_submit"]
        on_cancel_cb = self.current_dialog["on_cancel"]
        
        def next_field(e=None):
            if not self.current_dialog or self.current_dialog.get("type") != "input": return
            idx = self.current_dialog.get("index")
            if idx is None: return
            if idx < len(fields_copy) - 1:
                self.current_dialog["index"] += 1
                self.render_input_dialog(title)
            else:
                values = {f: dialog_fields[f].get() for f in fields_copy}
                self.current_dialog = None
                on_submit_cb(values)
        
        def cancel(e=None):
            if self.current_dialog:
                self.current_dialog = None
                on_cancel_cb()
        
        self.detail_text.bind("<Return>", next_field)
        self.detail_text.bind("<Escape>", cancel)
        self.detail_text.bind("<Key>", self.on_input_key)
        self.detail_text.focus()
    
    def on_input_key(self, e):
        if not self.current_dialog or self.current_dialog["type"] != "input" or e.keysym in ["Return", "Escape"]: return
        fields = self.current_dialog["field_order"]
        current_field = fields[self.current_dialog["index"]]
        if e.state & 0x4 and e.keysym == 'v':
            try:
                pasted = self.root.clipboard_get()
                self.current_dialog["fields"][current_field].set(self.current_dialog["fields"][current_field].get() + pasted)
            except:
                pass
            title = self.detail_text.get(1.0, "1.end")
            self.render_input_dialog(title)
            return
        if e.keysym == "BackSpace":
            val = self.current_dialog["fields"][current_field].get()
            self.current_dialog["fields"][current_field].set(val[:-1] if val else "")
        elif len(e.char) > 0 and ord(e.char) >= 32:
            self.current_dialog["fields"][current_field].set(self.current_dialog["fields"][current_field].get() + e.char)
        title = self.detail_text.get(1.0, "1.end")
        self.render_input_dialog(title)
    
    def add_platform(self):
        def on_submit(values):
            platform = values.get("Type Your Platform Name", "").strip()
            if not platform: self.show_message("Error", "Platform name required"); return
            if platform in self.manager.get_platforms(): self.show_message("Error", "Platform already exists"); return
            self.manager.vault.vault[platform] = []
            self.manager.vault.save()
            self.plat_combo['values'] = self.manager.get_platforms()
            self.plat_combo.set(platform)
            self.clear_details()
            self.show_message("Success", f"Added {platform}", lambda: self.create_main_screen())
        def on_cancel():
            self.clear_details()
        self.show_input_dialog("Add Platform", ["Type Your Platform Name"], on_submit, on_cancel)
    
    def del_platform(self):
        if not self.current_platform: self.show_message("Error", "Select a platform to delete"); return
        platform_to_delete = self.current_platform
        def on_yes():
            del self.manager.vault.vault[platform_to_delete]
            self.manager.vault.save()
            self.plat_combo['values'] = self.manager.get_platforms()
            self.plat_combo.set('')
            self.current_platform = None
            self.clear_details()
            self.show_message("Success", f"Platform '{platform_to_delete}' deleted", lambda: self.create_main_screen())
        def on_no():
            self.clear_details()
        self.show_confirmation("Delete Platform", f"Delete '{platform_to_delete}' and all credentials?", on_yes, on_no)

    def add_creds(self):
        if not self.current_platform: self.show_message("Error", "Select platform"); return
        def on_submit(values):
            u, pw, m = values.get("Type Your Username", "").strip(), values.get("Type Your Password", "").strip(), values.get("Type Your MFA Secret Key (optional)", "").strip()
            if not all([u, pw]): self.show_message("Error", "Username and Password required"); return
            success, msg = self.manager.add_cred(self.current_platform, u, pw, m or None)
            if success: self.show_message("Success", msg, lambda: self.create_main_screen())
            else: self.show_message("Error", msg)
        def on_cancel():
            self.clear_details()
        self.show_input_dialog("Add Credential", ["Type Your Username", "Type Your Password", "Type Your MFA Secret Key (optional)"], on_submit, on_cancel)
    
    def edit_creds(self):
        if not self.current_credential: self.show_message("Error", "Select credential"); return
        def on_submit(values):
            pw, m = values.get("Type Your New Password", "").strip(), values.get("Type Your New MFA Secret Key (optional)", "").strip()
            if not pw: self.show_message("Error", "Password required"); return
            success, msg = self.manager.edit_cred(self.current_platform, self.current_credential['username'], pw, m or None)
            if success: self.show_message("Success", msg, lambda: self.create_main_screen())
            else: self.show_message("Error", msg)
        def on_cancel():
            self.show_details()
        self.show_input_dialog("Edit Credential", ["Type Your New Password", "Type Your New MFA Secret Key (optional)"], on_submit, on_cancel)
    
    def del_creds(self):
        if not self.current_credential: self.show_message("Error", "Select credential"); return
        def on_yes():
            success, msg = self.manager.del_cred(self.current_platform, self.current_credential['username'])
            if success: self.show_message("Success", msg, lambda: self.create_main_screen())
            else: self.show_message("Error", msg)
        def on_no():
            self.show_details()
        self.show_confirmation("Confirm", f"Delete {self.current_credential['username']}?", on_yes, on_no)
    
    def on_logout(self):
        def on_yes():
            self.manager.crypto = None
            self.create_login_screen()
        def on_no():
            self.clear_details()
        self.show_confirmation("Logout", "Are you sure?", on_yes, on_no)
    
    def update_key(self):
        def on_submit(values):
            current_pwd = values.get("Type Your Current Master Key", "").strip()
            new_pwd = values.get("Type Your New Master Key", "").strip()
            confirm_pwd = values.get("Type Your New Master Key Again", "").strip()
            
            if not current_pwd: self.show_message("Error", "Current master key required"); return
            if not new_pwd: self.show_message("Error", "New master key required"); return
            if new_pwd != confirm_pwd: self.show_message("Error", "Passwords don't match"); return
            if not cred.verify_master_key(current_pwd): self.show_message("Error", "❌ Incorrect current master key"); return
            
            success, msg = cred.rotate_master_key(current_pwd, new_pwd)
            if success:
                self.manager.crypto = Crypto(new_pwd)
                self.manager.master_key = new_pwd
                self.manager.vault.set_crypto(self.manager.crypto)
                self.manager.vault.load()
                self.create_login_screen()
                
            else:
                self.show_message("Error", msg)
        def on_cancel():
            self.clear_details()
        
        self.show_input_dialog("CHANGE MASTER KEY", ["Type Your Current Master Key", "Type Your New Master Key", "Type Your New Master Key Again"], on_submit, on_cancel)
    
    def export_credentials(self):
        def on_yes():
            result = export_credentials_to_excel(self.manager.master_key)
            if result["success"]:
                self.show_message("Success ✅", f"Exported to Desktop!\n\nFile: credentials.xlsx", lambda: self.create_main_screen())
            else:
                self.show_message("Error", result["message"])
        
        def on_no():
            self.show_message("Cancelled", "Export aborted", lambda: self.clear_details())
        
        self.show_confirmation("Export Credentials", "⚠️ This will download DECRYPTED passwords to Excel.\n\nProceed?", on_yes, on_no)

root = tk.Tk()
root.resizable(False, False)
style = ttk.Style()
style.configure("TCombobox", fieldbackground=COLOR_BG_DARK, background=COLOR_BG_DARK, foreground=COLOR_TEXT_PRIMARY, highlightthickness=0, relief="flat")
style.theme_use('clam')
gui = CredentialManagerGUI(root)
root.mainloop()
