import json, os, tkinter as tk
from tkinter import ttk, messagebox
import sys
sys.path.insert(0, '..')
from classes import Crypto
from config import COLOR_BG_DARK, COLOR_BG_MEDIUM, COLOR_ACCENT, COLOR_TEXT_PRIMARY, COLOR_ERROR

CREDENTIALS_FILE = "credentials.json"

class CredentialManager:
    def __init__(self):
        self.crypto = None
        self.credentials = self._load_credentials()
    
    def setup_master_password(self, password):
        if not password: return False
        self.crypto = Crypto(password)
        return True
    
    def _load_credentials(self):
        if os.path.exists(CREDENTIALS_FILE):
            try:
                with open(CREDENTIALS_FILE, 'r') as f: return json.load(f)
            except: return {}
        return {}
    
    def _save_credentials(self):
        try:
            with open(CREDENTIALS_FILE, 'w') as f: json.dump(self.credentials, f, indent=4)
            return True, "Saved"
        except Exception as e: return False, str(e)
    
    def add_credential(self, platform, username, password, mfa=None):
        if not self.crypto: return False, "No password set"
        if platform in self.credentials and username in [c['username'] for c in self.credentials[platform]]: return False, "Username exists"
        encrypted_password = self.crypto.encrypt_aes(password)
        encrypted_secret = self.crypto.encrypt_aes(mfa) if mfa else None
        if platform not in self.credentials: self.credentials[platform] = []
        credential = {'username': username, 'password': encrypted_password}
        if encrypted_secret: credential['mfa'] = encrypted_secret
        self.credentials[platform].append(credential)
        success, msg = self._save_credentials()
        return (True, f"Added {username}") if success else (False, msg)
    
    def edit_credential(self, platform, username, new_password=None, new_mfa=None):
        if not self.crypto: return False, "No password set"
        if platform not in self.credentials: return False, "Platform not found"
        for cred in self.credentials[platform]:
            if cred['username'] == username:
                if new_password: cred['password'] = self.crypto.encrypt_aes(new_password)
                if new_mfa is not None:
                    if new_mfa: cred['mfa'] = self.crypto.encrypt_aes(new_mfa)
                    elif 'mfa' in cred: del cred['mfa']
                success, msg = self._save_credentials()
                return (True, f"Updated {username}") if success else (False, msg)
        return False, "Username not found"
    
    def delete_credential(self, platform, username):
        if not self.crypto: return False, "No password set"
        if platform not in self.credentials: return False, "Platform not found"
        for i, cred in enumerate(self.credentials[platform]):
            if cred['username'] == username:
                self.credentials[platform].pop(i)
                if not self.credentials[platform]: del self.credentials[platform]
                success, msg = self._save_credentials()
                return (True, f"Deleted {username}") if success else (False, msg)
        return False, "Username not found"
    
    def get_platforms(self): return sorted(self.credentials.keys())
    
    def get_credentials_for_platform(self, platform):
        if platform not in self.credentials or not self.crypto: return []
        result = []
        for cred in self.credentials[platform]:
            try:
                pwd = self.crypto.decrypt_aes(cred['password'])
                mfa = self.crypto.decrypt_aes(cred.get('mfa')) if cred.get('mfa') else None
                result.append({'username': cred['username'], 'password': pwd, 'mfa': mfa})
            except: pass
        return result


class CredentialManagerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Password Manager - Dropdown")
        self.root.geometry("650x350")
        self.root.configure(bg=COLOR_BG_DARK)
        self.manager = CredentialManager()
        self.current_platform = None
        self.current_credential = None
        self._create_login_screen()
    
    def _create_login_screen(self):
        for widget in self.root.winfo_children(): widget.destroy()
        frame = tk.Frame(self.root, bg=COLOR_BG_DARK)
        frame.pack(expand=True, fill="both", padx=20, pady=20)
        tk.Label(frame, text="🔐 Password Manager", font=("Segoe UI", 24, "bold"), bg=COLOR_BG_DARK, fg=COLOR_ACCENT).pack(pady=20)
        tk.Label(frame, text="Enter Master Password", font=("Segoe UI", 12), bg=COLOR_BG_DARK, fg=COLOR_TEXT_PRIMARY).pack(pady=10)
        password_var = tk.StringVar()
        password_entry = tk.Entry(frame, textvariable=password_var, show="•", font=("Segoe UI", 11), width=30)
        password_entry.pack(pady=10)
        password_entry.focus()
        def login():
            if self.manager.setup_master_password(password_var.get()): self._create_main_screen()
            else: messagebox.showerror("Error", "Failed")
        tk.Button(frame, text="Login", command=login, font=("Segoe UI", 11), bg=COLOR_ACCENT, fg=COLOR_BG_DARK, padx=20, pady=10, relief="flat").pack(pady=20)
        password_entry.bind("<Return>", lambda e: login())
    
    def _create_main_screen(self):
        for widget in self.root.winfo_children(): widget.destroy()
        header = tk.Frame(self.root, bg=COLOR_BG_MEDIUM, height=50)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text="🔐 Password Manager", font=("Segoe UI", 16, "bold"), bg=COLOR_BG_MEDIUM, fg=COLOR_ACCENT).pack(side="left", padx=20, pady=10)
        tk.Button(header, text="🚪 Logout", command=self._logout, font=("Segoe UI", 10), bg=COLOR_ERROR, fg="white", relief="flat", padx=10, pady=5).pack(side="right", padx=20, pady=10)
        
        content = tk.Frame(self.root, bg=COLOR_BG_DARK)
        content.pack(fill="both", expand=False, padx=20, pady=20)
        
        sel_frame = tk.Frame(content, bg=COLOR_BG_DARK)
        sel_frame.pack(fill="x", pady=(0, 15))
        
        tk.Label(sel_frame, text="📋 Platform:", font=("Segoe UI", 11, "bold"), bg=COLOR_BG_DARK, fg=COLOR_ACCENT).pack(side="left", padx=(0, 10))
        self.plat_combo = ttk.Combobox(sel_frame, font=("Segoe UI", 10), state="readonly", width=25)
        self.plat_combo['values'] = self.manager.get_platforms()
        self.plat_combo.pack(side="left", padx=(0, 20))
        self.plat_combo.bind("<<ComboboxSelected>>", self._on_platform_change)
        
        tk.Label(sel_frame, text="🔑 User:", font=("Segoe UI", 11, "bold"), bg=COLOR_BG_DARK, fg=COLOR_ACCENT).pack(side="left", padx=(0, 10))
        self.user_combo = ttk.Combobox(sel_frame, font=("Segoe UI", 10), state="readonly", width=25)
        self.user_combo.pack(side="left")
        self.user_combo.bind("<<ComboboxSelected>>", self._on_credential_change)
        
        detail_frame = tk.Frame(content, bg=COLOR_BG_MEDIUM, relief="flat")
        detail_frame.pack(fill="both", expand=False, pady=(0, 15))
        
        self.detail_text = tk.Text(detail_frame, font=("Segoe UI", 10), bg=COLOR_BG_DARK, fg=COLOR_TEXT_PRIMARY, relief="flat", padx=15, pady=15, wrap="word", height=8, width=70)
        self.detail_text.pack(fill="both", expand=False, padx=1, pady=1)
        self.detail_text.config(state="disabled")
        
        btn_frame = tk.Frame(content, bg=COLOR_BG_DARK)
        btn_frame.pack(fill="x")
        tk.Button(btn_frame, text="➕ Add", command=self._add_credential, font=("Segoe UI", 10), bg=COLOR_ACCENT, fg=COLOR_BG_DARK, relief="flat", padx=15, pady=8).pack(side="left", padx=5)
        tk.Button(btn_frame, text="✏️ Edit", command=self._edit_credential, font=("Segoe UI", 10), bg=COLOR_ACCENT, fg=COLOR_BG_DARK, relief="flat", padx=15, pady=8).pack(side="left", padx=5)
        tk.Button(btn_frame, text="🗑️ Delete", command=self._delete_credential, font=("Segoe UI", 10), bg=COLOR_ERROR, fg="white", relief="flat", padx=15, pady=8).pack(side="left", padx=5)
    
    def _on_platform_change(self, event):
        self.current_platform = self.plat_combo.get()
        self.user_combo['values'] = [c['username'] for c in self.manager.get_credentials_for_platform(self.current_platform)]
        self.user_combo.set('')
        self._clear_details()
    
    def _on_credential_change(self, event):
        if not self.current_platform: return
        username = self.user_combo.get()
        creds = self.manager.get_credentials_for_platform(self.current_platform)
        for c in creds:
            if c['username'] == username:
                self.current_credential = c
                self._show_details()
                break
    
    def _show_details(self):
        if not self.current_credential: return
        c = self.current_credential
        text = f"Platform: {self.current_platform}\n\nUsername: {c['username']}\n\nPassword: {c['password']}\n"
        text += f"\nMFA: {c['mfa'] if c['mfa'] else 'MFA not configured'}"
        self.detail_text.config(state="normal")
        self.detail_text.delete(1.0, "end")
        self.detail_text.insert(1.0, text)
        self.detail_text.config(state="disabled")
    
    def _clear_details(self):
        self.detail_text.config(state="normal")
        self.detail_text.delete(1.0, "end")
        self.detail_text.config(state="disabled")
    
    def _add_credential(self):
        if not self.current_platform: messagebox.showerror("Error", "Select platform"); return
        d = tk.Toplevel(self.root)
        d.title("Add Credential")
        d.geometry("400x250")
        d.configure(bg=COLOR_BG_DARK)
        tk.Label(d, text="Username:", font=("Segoe UI", 10), bg=COLOR_BG_DARK, fg=COLOR_TEXT_PRIMARY).pack(pady=3)
        uvar = tk.StringVar()
        tk.Entry(d, textvariable=uvar, font=("Segoe UI", 10), width=40).pack(pady=3)
        tk.Label(d, text="Password:", font=("Segoe UI", 10), bg=COLOR_BG_DARK, fg=COLOR_TEXT_PRIMARY).pack(pady=3)
        pwvar = tk.StringVar()
        tk.Entry(d, textvariable=pwvar, font=("Segoe UI", 10), width=40).pack(pady=3)
        tk.Label(d, text="MFA (optional):", font=("Segoe UI", 10), bg=COLOR_BG_DARK, fg=COLOR_TEXT_PRIMARY).pack(pady=3)
        mvar = tk.StringVar()
        tk.Entry(d, textvariable=mvar, font=("Segoe UI", 10), width=40).pack(pady=3)
        def save():
            u, pw, m = uvar.get().strip(), pwvar.get().strip(), mvar.get().strip()
            if not all([u, pw]): messagebox.showerror("Error", "Required", parent=d); return
            success, msg = self.manager.add_credential(self.current_platform, u, pw, m or None)
            if success: d.destroy(); self._create_main_screen(); messagebox.showinfo("Success", msg)
            else: messagebox.showerror("Error", msg, parent=d)
        tk.Button(d, text="Save", command=save, font=("Segoe UI", 10), bg=COLOR_ACCENT, fg=COLOR_BG_DARK, relief="flat", padx=20, pady=5).pack(pady=10)
    
    def _edit_credential(self):
        if not self.current_credential: messagebox.showerror("Error", "Select credential"); return
        d = tk.Toplevel(self.root)
        d.title("Edit Credential")
        d.geometry("400x250")
        d.configure(bg=COLOR_BG_DARK)
        tk.Label(d, text="Password:", font=("Segoe UI", 10), bg=COLOR_BG_DARK, fg=COLOR_TEXT_PRIMARY).pack(pady=3)
        pwvar = tk.StringVar(value=self.current_credential['password'])
        tk.Entry(d, textvariable=pwvar, font=("Segoe UI", 10), width=40).pack(pady=3)
        tk.Label(d, text="MFA (optional):", font=("Segoe UI", 10), bg=COLOR_BG_DARK, fg=COLOR_TEXT_PRIMARY).pack(pady=3)
        mvar = tk.StringVar(value=self.current_credential['mfa'] or "")
        tk.Entry(d, textvariable=mvar, font=("Segoe UI", 10), width=40).pack(pady=3)
        def save():
            pw, m = pwvar.get().strip(), mvar.get().strip()
            if not pw: messagebox.showerror("Error", "Password required", parent=d); return
            success, msg = self.manager.edit_credential(self.current_platform, self.current_credential['username'], pw, m or None)
            if success: d.destroy(); self._create_main_screen(); messagebox.showinfo("Success", msg)
            else: messagebox.showerror("Error", msg, parent=d)
        tk.Button(d, text="Save", command=save, font=("Segoe UI", 10), bg=COLOR_ACCENT, fg=COLOR_BG_DARK, relief="flat", padx=20, pady=5).pack(pady=10)
    
    def _delete_credential(self):
        if not self.current_credential: messagebox.showerror("Error", "Select credential"); return
        if messagebox.askyesno("Confirm", f"Delete {self.current_credential['username']}?"):
            success, msg = self.manager.delete_credential(self.current_platform, self.current_credential['username'])
            if success: self._create_main_screen(); messagebox.showinfo("Success", msg)
            else: messagebox.showerror("Error", msg)
    
    def _logout(self):
        if messagebox.askyesno("Logout", "Sure?"): self.manager.crypto = None; self._create_login_screen()

def main():
    root = tk.Tk()
    style = ttk.Style()
    style.theme_use('clam')
    gui = CredentialManagerGUI(root)
    root.mainloop()

if __name__ == "__main__": main()
