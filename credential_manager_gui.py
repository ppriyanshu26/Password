import tkinter as tk
from tkinter import ttk
from classes import Crypto
from config import COLOR_BG_DARK, COLOR_BG_MEDIUM, COLOR_ACCENT, COLOR_TEXT_PRIMARY, COLOR_ERROR
import credentials as cred
from utils import export_credentials_to_excel

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
            return True
        if cred.verify_master_key(password):
            self.crypto = Crypto(password)
            self.master_key = password
            self.vault.set_crypto(self.crypto)
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
    
    def get_credentials_for_platform(self, platform):
        return self.vault.get_credentials_for_platform(platform)

class CredentialManagerGUI:
    def __init__(self, root):
        self.root = root; self.root.title("Password Manager"); self.root.geometry("650x350"); self.root.configure(bg=COLOR_BG_DARK); self.manager = CredentialManager(); self.current_platform = None; self.current_credential = None; self.detail_text = None; self.current_dialog = None; self.create_login_screen()
    
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
        self.plat_combo = ttk.Combobox(sel_frame, font=("Segoe UI", 10), state="readonly", width=25)
        self.plat_combo['values'] = self.manager.get_platforms()
        self.plat_combo.pack(side="left", padx=(0, 10))
        self.plat_combo.bind("<<ComboboxSelected>>", self.platform_change)
        tk.Button(sel_frame, text="➕", command=self.add_platform, font=("Segoe UI", 10), bg=COLOR_ACCENT, fg=COLOR_BG_DARK, relief="flat", padx=8, pady=3).pack(side="left", padx=(0, 20))
        
        tk.Label(sel_frame, text="🔑 User:", font=("Segoe UI", 11, "bold"), bg=COLOR_BG_DARK, fg=COLOR_ACCENT).pack(side="left", padx=(0, 10))
        self.user_combo = ttk.Combobox(sel_frame, font=("Segoe UI", 10), state="readonly", width=25)
        self.user_combo.pack(side="left")
        self.user_combo.bind("<<ComboboxSelected>>", self.credential_change)
        
        detail_frame = tk.Frame(content, bg=COLOR_BG_MEDIUM, relief="flat")
        detail_frame.pack(fill="both", expand=False, pady=(0, 15))
        
        self.detail_text = tk.Text(detail_frame, font=("Segoe UI", 10), bg=COLOR_BG_DARK, fg=COLOR_TEXT_PRIMARY, relief="flat", padx=15, pady=15, wrap="word", height=8, width=70)
        self.detail_text.pack(fill="both", expand=False, padx=1, pady=1)
        self.detail_text.config(state="disabled")
        
        btn_frame = tk.Frame(content, bg=COLOR_BG_DARK)
        btn_frame.pack(fill="x")
        tk.Button(btn_frame, text="➕ Add", command=self.add_creds, font=("Segoe UI", 10), bg=COLOR_ACCENT, fg=COLOR_BG_DARK, relief="flat", padx=15, pady=8).pack(side="left", padx=5)
        tk.Button(btn_frame, text="✏️ Edit", command=self.edit_creds, font=("Segoe UI", 10), bg=COLOR_ACCENT, fg=COLOR_BG_DARK, relief="flat", padx=15, pady=8).pack(side="left", padx=5)
        tk.Button(btn_frame, text="🗑️ Delete", command=self.del_creds, font=("Segoe UI", 10), bg=COLOR_ERROR, fg="white", relief="flat", padx=15, pady=8).pack(side="left", padx=5)
        tk.Button(btn_frame, text="🔐 Change Master Key", command=self.update_key, font=("Segoe UI", 10), bg="#FFA500", fg="white", relief="flat", padx=15, pady=8).pack(side="left", padx=5)
        tk.Button(btn_frame, text="⬇️ Export", command=self.export_credentials, font=("Segoe UI", 10), bg="#4CAF50", fg="white", relief="flat", padx=15, pady=8).pack(side="left", padx=5)
    
    def platform_change(self, event):
        self.current_platform = self.plat_combo.get()
        self.user_combo['values'] = [c['username'] for c in self.manager.get_credentials_for_platform(self.current_platform)]
        self.user_combo.set('')
        self.clear_details()
    
    def credential_change(self, event):
        if not self.current_platform: return
        username = self.user_combo.get()
        creds = self.manager.get_credentials_for_platform(self.current_platform)
        for c in creds:
            if c['username'] == username:
                self.current_credential = c
                self.show_details()
                break

    def show_details(self):
        if not self.current_credential: return
        c = self.current_credential
        text = f"Platform: {self.current_platform}\n\nUsername: {c['username']}\n\nPassword: {c['password']}\n"
        text += f"\nMFA: {c['mfa'] if c['mfa'] else 'MFA not configured'}"
        self.detail_text.config(state="normal")
        self.detail_text.delete(1.0, "end")
        self.detail_text.insert(1.0, text)
        self.detail_text.config(state="disabled")
    
    def clear_details(self):
        self.detail_text.config(state="normal")
        self.detail_text.delete(1.0, "end")
        self.detail_text.config(state="disabled")
    
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
        if e.keysym == "BackSpace":
            val = self.current_dialog["fields"][current_field].get()
            self.current_dialog["fields"][current_field].set(val[:-1] if val else "")
        elif len(e.char) > 0 and ord(e.char) >= 32:
            self.current_dialog["fields"][current_field].set(self.current_dialog["fields"][current_field].get() + e.char)
        title = self.detail_text.get(1.0, "1.end")
        self.render_input_dialog(title)
    
    def add_platform(self):
        def on_submit(values):
            platform = values.get("Platform Name", "").strip()
            if not platform: self.show_message("Error", "Platform name required"); return
            if platform in self.manager.get_platforms(): self.show_message("Error", "Platform already exists"); return
            self.manager.vault.vault[platform] = []
            self.manager.vault.save()
            self.show_message("Success", f"Added {platform}", lambda: self.create_main_screen())
        def on_cancel():
            self.clear_details()
        self.show_input_dialog("Add Platform", ["Type Your Platform Name"], on_submit, on_cancel)
    
    def add_creds(self):
        if not self.current_platform: self.show_message("Error", "Select platform"); return
        def on_submit(values):
            u, pw, m = values.get("Username", "").strip(), values.get("Password", "").strip(), values.get("MFA (optional)", "").strip()
            if not all([u, pw]): self.show_message("Error", "Username and Password required"); return
            success, msg = self.manager.add_cred(self.current_platform, u, pw, m or None)
            if success: self.show_message("Success", msg, lambda: self.create_main_screen())
            else: self.show_message("Error", msg)
        def on_cancel():
            self.clear_details()
        self.show_input_dialog("Add Credential", ["Type Your Username", "Type Your Password", "Type Your MFA Secret Code (optional)"], on_submit, on_cancel)
    
    def edit_creds(self):
        if not self.current_credential: self.show_message("Error", "Select credential"); return
        def on_submit(values):
            pw, m = values.get("Password", "").strip(), values.get("MFA (optional)", "").strip()
            if not pw: self.show_message("Error", "Password required"); return
            success, msg = self.manager.edit_cred(self.current_platform, self.current_credential['username'], pw, m or None)
            if success: self.show_message("Success", msg, lambda: self.create_main_screen())
            else: self.show_message("Error", msg)
        def on_cancel():
            self.show_details()
        self.show_input_dialog("Edit Credential", ["Type Your Password", "Type Your MFA Secret Code (optional)"], on_submit, on_cancel)
    
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
            current_pwd = values.get("Current Master Key", "").strip()
            new_pwd = values.get("New Master Key", "").strip()
            confirm_pwd = values.get("Confirm New Master Key", "").strip()
            
            if not current_pwd: self.show_message("Error", "Current master key required"); return
            if not new_pwd: self.show_message("Error", "New master key required"); return
            if new_pwd != confirm_pwd: self.show_message("Error", "Passwords don't match"); return
            
            if not cred.verify_master_key(current_pwd): self.show_message("Error", "❌ Incorrect current master key"); return
            
            cred.save_master_key(new_pwd)
            self.manager.crypto = Crypto(new_pwd)
            self.manager.vault.set_crypto(self.manager.crypto)
            self.show_message("Success", "Master key changed successfully", lambda: self.create_main_screen())
        
        def on_cancel():
            self.clear_details()
        
        self.show_input_dialog("CHANGE MASTER KEY", ["Type Your Current Master Key", "Type Your New Master Key", "Type Your Confirm New Master Key"], on_submit, on_cancel)
    
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
style = ttk.Style()
style.theme_use('clam')
gui = CredentialManagerGUI(root)
root.mainloop()
