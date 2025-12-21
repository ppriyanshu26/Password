from config import WINDOW_TITLE, WINDOW_SIZE
import tkinter as tk
from tkinter import ttk
from core import (load_master_key_hash, save_master_key_hash, verify_master_key,
                       get_platforms, get_accounts_for_platform, add_credential,
                       delete_credential, update_credential)

class CredentialEditorApp:
    def __init__(self, parent=None):
        self.root = tk.Toplevel(parent) if parent else tk.Tk()
        self.root.withdraw()
        self.root.title(WINDOW_TITLE)
        self.root.configure(bg="#1a1a1a")
        self.root.resizable(False, False)
        self.master_key = None
        self.msg_label = None
        self.root.geometry(WINDOW_SIZE)
        self.center_window()
        self.show_login_screen()
        self.root.deiconify()
    
    def show_message(self, msg, success=True):
        if self.msg_label:
            self.msg_label.config(text=msg, fg="#4CAF50" if success else "#ff4444")
        
    def clear_message(self):
        if self.msg_label:
            self.msg_label.config(text="")
    
    def center_window(self):
        self.root.update_idletasks()
        w, h = self.root.winfo_width(), self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (w // 2)
        y = (self.root.winfo_screenheight() // 2) - (h // 2)
        self.root.geometry(f"+{x}+{y}")
    
    def clear_window(self):
        for w in self.root.winfo_children():
            w.destroy()
    
    def show_login_screen(self):
        self.clear_window()
        
        frame = tk.Frame(self.root, bg="#1a1a1a", padx=30, pady=30)
        frame.pack(expand=True, fill="both")
        
        tk.Label(frame, text="🔐 Master Key", fg="white", bg="#1a1a1a", font=("Segoe UI", 14, "bold")).pack(pady=(0, 20))
        
        msg = "No master key set. Enter a new master key:" if load_master_key_hash() is None else "Enter your master key:"
        tk.Label(frame, text=msg, fg="#888", bg="#1a1a1a", font=("Segoe UI", 9)).pack(anchor="w")
        
        self.key_entry = tk.Entry(frame, show="*", bg="#333", fg="white", insertbackground="white", bd=0, font=("Segoe UI", 11), width=30)
        self.key_entry.pack(fill="x", pady=(5, 10), ipady=8)
        self.key_entry.focus_set()
        self.key_entry.bind("<Return>", lambda e: self.verify_key())
        
        self.msg_label = tk.Label(frame, text="", bg="#1a1a1a", font=("Segoe UI", 9))
        self.msg_label.pack(pady=(0, 5))
        
        btn_frame = tk.Frame(frame, bg="#1a1a1a")
        btn_frame.pack(fill="x")
        
        tk.Button(btn_frame, text="Unlock", command=self.verify_key, bg="#4CAF50", fg="white", activebackground="#45a049", activeforeground="white", bd=0, font=("Segoe UI", 10), cursor="hand2", width=15).pack(side="left", padx=(0, 5))
        tk.Button(btn_frame, text="Cancel", command=self.root.destroy, bg="#444", fg="white", activebackground="#555", activeforeground="white", bd=0, font=("Segoe UI", 10), cursor="hand2", width=15).pack(side="right")
        
        self.root.bind("<Escape>", lambda e: self.root.destroy())
    
    def verify_key(self):
        key = self.key_entry.get()
        if not key:
            self.show_message("Please enter a master key", False)
            return
        
        stored = load_master_key_hash()
        if stored is None:
            save_master_key_hash(key)
            self.master_key = key
            self.show_main_screen()
        elif verify_master_key(key):
            self.master_key = key
            self.show_main_screen()
        else:
            self.show_message("Invalid master key", False)
            self.key_entry.delete(0, tk.END)
    
    def show_main_screen(self):
        self.clear_window()
        
        main_frame = tk.Frame(self.root, bg="#1a1a1a", padx=20, pady=15)
        main_frame.pack(expand=True, fill="both")
        
        header = tk.Frame(main_frame, bg="#1a1a1a")
        header.pack(fill="x", pady=(0, 15))
        tk.Label(header, text="📋 Credential Manager", fg="white", bg="#1a1a1a", font=("Segoe UI", 14, "bold")).pack(side="left")
        tk.Button(header, text="➕ Add New", command=self.show_add_screen, bg="#4CAF50", fg="white", activebackground="#45a049", activeforeground="white", bd=0, font=("Segoe UI", 9), cursor="hand2").pack(side="right")
        
        plat_frame = tk.Frame(main_frame, bg="#1a1a1a")
        plat_frame.pack(fill="x", pady=(0, 10))
        tk.Label(plat_frame, text="Platform:", fg="white", bg="#1a1a1a", font=("Segoe UI", 12)).pack(side="left", padx=(0, 10))
        
        self.platform_var = tk.StringVar()
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TCombobox", fieldbackground="#333", background="#333", foreground="white", arrowcolor="white", font=("Segoe UI", 12))
        style.map("TCombobox", fieldbackground=[("readonly", "#333")])
        self.root.option_add("*TCombobox*Listbox.font", ("Segoe UI", 12))
        self.root.option_add("*TCombobox*Listbox.background", "#333")
        self.root.option_add("*TCombobox*Listbox.foreground", "white")
        
        self.platform_combo = ttk.Combobox(plat_frame, textvariable=self.platform_var, values=get_platforms(), state="readonly", width=25, font=("Segoe UI", 12))
        self.platform_combo.pack(side="left", fill="x", expand=True)
        self.platform_combo.bind("<<ComboboxSelected>>", self.on_platform_select)
        
        self.msg_label = tk.Label(main_frame, text="", bg="#1a1a1a", font=("Segoe UI", 9))
        self.msg_label.pack(pady=(5, 0))
        
        tk.Label(main_frame, text="Accounts:", fg="white", bg="#1a1a1a", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(10, 5))
        
        container = tk.Frame(main_frame, bg="#252525", bd=1, relief="solid")
        container.pack(fill="both", expand=True, pady=(0, 10))
        
        canvas = tk.Canvas(container, bg="#252525", highlightthickness=0)
        scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
        self.accounts_frame = tk.Frame(canvas, bg="#252525")
        self.accounts_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.accounts_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        scrollbar.pack(side="right", fill="y")
        
        tk.Label(self.accounts_frame, text="Select a platform to view accounts", fg="#888", bg="#252525", font=("Segoe UI", 9, "italic")).pack(pady=20)
        
        tk.Button(main_frame, text="Close", command=self.root.destroy, bg="#444", fg="white", activebackground="#555", activeforeground="white", bd=0, font=("Segoe UI", 10), cursor="hand2", width=15).pack(side="right")
    
    def on_platform_select(self, event=None):
        platform = self.platform_var.get()
        if not platform:
            return
        
        for w in self.accounts_frame.winfo_children():
            w.destroy()
        
        accounts = get_accounts_for_platform(platform)
        if not accounts:
            tk.Label(self.accounts_frame, text="No accounts for this platform", fg="#888", bg="#252525", font=("Segoe UI", 9, "italic")).pack(pady=20)
            return
        
        for acc in accounts:
            self.create_account_row(platform, acc)
    
    def create_account_row(self, platform, acc):
        row = tk.Frame(self.accounts_frame, bg="#333", padx=15, pady=12)
        row.pack(fill="x", pady=4, padx=4)
        tk.Label(row, text=f"👤 {acc['username']}", fg="white", bg="#333", font=("Segoe UI", 17)).pack(side="left")
        
        btns = tk.Frame(row, bg="#333")
        btns.pack(side="right")
        edit_btn = tk.Button(btns, text="✏️", command=lambda p=platform, a=acc: self.show_edit_screen(p, a), bg="#444", fg="white", activebackground="#555", activeforeground="white", bd=0, font=("Segoe UI Emoji", 12), cursor="hand2", padx=10, pady=4)
        edit_btn.pack(side="left", padx=4)
        del_btn = tk.Button(btns, text="🗑️", command=lambda p=platform, u=acc['username']: self.confirm_delete(p, u), bg="#444", fg="white", activebackground="#555", activeforeground="#ff4444", bd=0, font=("Segoe UI Emoji", 12), cursor="hand2", padx=10, pady=4)
        del_btn.pack(side="left", padx=4)
    
    def confirm_delete(self, platform, username):
        self.show_delete_confirm(platform, username)
    
    def show_delete_confirm(self, platform, username):
        for w in self.accounts_frame.winfo_children():
            w.destroy()
        
        tk.Label(self.accounts_frame, text=f"Delete '{username}'?", fg="#ff4444", bg="#252525", font=("Segoe UI", 10, "bold")).pack(pady=(20, 10))
        
        btn_frame = tk.Frame(self.accounts_frame, bg="#252525")
        btn_frame.pack()
        tk.Button(btn_frame, text="Yes", command=lambda: self.do_delete(platform, username), bg="#ff4444", fg="white", activebackground="#cc3333", activeforeground="white", bd=0, font=("Segoe UI", 9), cursor="hand2", width=8).pack(side="left", padx=5)
        tk.Button(btn_frame, text="No", command=self.on_platform_select, bg="#444", fg="white", activebackground="#555", activeforeground="white", bd=0, font=("Segoe UI", 9), cursor="hand2", width=8).pack(side="left", padx=5)
        
        self.root.bind("<Return>", lambda e: self.do_delete(platform, username))
        self.root.bind("<Escape>", lambda e: self.on_platform_select())
    
    def do_delete(self, platform, username):
        success, msg = delete_credential(platform, username)
        if success:
            self.show_message(msg, True)
            platforms = get_platforms()
            self.platform_combo['values'] = platforms
            if platform in platforms:
                self.on_platform_select()
            else:
                self.platform_var.set('')
                for w in self.accounts_frame.winfo_children():
                    w.destroy()
                tk.Label(self.accounts_frame, text="Select a platform to view accounts", fg="#888", bg="#252525", font=("Segoe UI", 9, "italic")).pack(pady=20)
        else:
            self.show_message(msg, False)
            self.on_platform_select()
    
    def show_add_screen(self):
        self.clear_window()
        
        frame = tk.Frame(self.root, bg="#1a1a1a", padx=30, pady=20)
        frame.pack(expand=True, fill="both")
        tk.Label(frame, text="➕ Add New Credential", fg="white", bg="#1a1a1a", font=("Segoe UI", 14, "bold")).pack(pady=(0, 15))
        
        self.msg_label = tk.Label(frame, text="", bg="#1a1a1a", font=("Segoe UI", 9))
        self.msg_label.pack(pady=(0, 5))
        
        tk.Label(frame, text="Platform *", fg="#888", bg="#1a1a1a", font=("Segoe UI", 9)).pack(anchor="w")
        self.add_platform = tk.Entry(frame, bg="#333", fg="white", insertbackground="white", bd=0, font=("Segoe UI", 10))
        self.add_platform.pack(fill="x", pady=(2, 10), ipady=6)
        
        tk.Label(frame, text="Username *", fg="#888", bg="#1a1a1a", font=("Segoe UI", 9)).pack(anchor="w")
        self.add_username = tk.Entry(frame, bg="#333", fg="white", insertbackground="white", bd=0, font=("Segoe UI", 10))
        self.add_username.pack(fill="x", pady=(2, 10), ipady=6)
        
        tk.Label(frame, text="Password *", fg="#888", bg="#1a1a1a", font=("Segoe UI", 9)).pack(anchor="w")
        self.add_password = tk.Entry(frame, show="*", bg="#333", fg="white", insertbackground="white", bd=0, font=("Segoe UI", 10))
        self.add_password.pack(fill="x", pady=(2, 10), ipady=6)
        
        tk.Label(frame, text="TOTP Secret (optional)", fg="#888", bg="#1a1a1a", font=("Segoe UI", 9)).pack(anchor="w")
        self.add_secretco = tk.Entry(frame, bg="#333", fg="white", insertbackground="white", bd=0, font=("Segoe UI", 10))
        self.add_secretco.pack(fill="x", pady=(2, 10), ipady=6)
        
        btns = tk.Frame(frame, bg="#1a1a1a")
        btns.pack(fill="x")
        tk.Button(btns, text="Save", command=self.save_new_credential, bg="#4CAF50", fg="white", activebackground="#45a049", activeforeground="white", bd=0, font=("Segoe UI", 10), cursor="hand2", width=12).pack(side="left")
        tk.Button(btns, text="Cancel", command=self.show_main_screen, bg="#444", fg="white", activebackground="#555", activeforeground="white", bd=0, font=("Segoe UI", 10), cursor="hand2", width=12).pack(side="right")
        
        self.root.bind("<Return>", lambda e: self.save_new_credential())
        self.root.bind("<Escape>", lambda e: self.show_main_screen())
    
    def save_new_credential(self):
        platform = self.add_platform.get().strip().lower()
        username = self.add_username.get().strip()
        password = self.add_password.get()
        secretco = self.add_secretco.get().strip()
        
        if not platform or not username or not password:
            self.show_message("Platform, Username and Password are required", False)
            return
        
        success, msg = add_credential(platform, username, password, secretco, self.master_key)
        if success:
            self.show_main_screen()
            self.show_message(msg, True)
        else:
            self.show_message(msg, False)
    
    def show_edit_screen(self, platform, acc):
        self.clear_window()
        
        frame = tk.Frame(self.root, bg="#1a1a1a", padx=30, pady=20)
        frame.pack(expand=True, fill="both")
        tk.Label(frame, text=f"✏️ Edit: {acc['username']}", fg="white", bg="#1a1a1a", font=("Segoe UI", 14, "bold")).pack(pady=(0, 5))
        tk.Label(frame, text=f"Platform: {platform}", fg="#888", bg="#1a1a1a", font=("Segoe UI", 9)).pack(pady=(0, 10))
        
        self.msg_label = tk.Label(frame, text="", bg="#1a1a1a", font=("Segoe UI", 9))
        self.msg_label.pack(pady=(0, 10))
        
        tk.Label(frame, text="New Password (leave empty to keep current)", fg="#888", bg="#1a1a1a", font=("Segoe UI", 9)).pack(anchor="w")
        self.edit_password = tk.Entry(frame, show="*", bg="#333", fg="white", insertbackground="white", bd=0, font=("Segoe UI", 10))
        self.edit_password.pack(fill="x", pady=(2, 10), ipady=6)
        
        label = "New TOTP Secret (leave empty to keep current)" if "secretco" in acc else "TOTP Secret (optional)"
        tk.Label(frame, text=label, fg="#888", bg="#1a1a1a", font=("Segoe UI", 9)).pack(anchor="w")
        self.edit_secretco = tk.Entry(frame, bg="#333", fg="white", insertbackground="white", bd=0, font=("Segoe UI", 10))
        self.edit_secretco.pack(fill="x", pady=(2, 15), ipady=6)
        
        btns = tk.Frame(frame, bg="#1a1a1a")
        btns.pack(fill="x")
        tk.Button(btns, text="Save", command=lambda: self.save_edit(platform, acc['username']), bg="#4CAF50", fg="white", activebackground="#45a049", activeforeground="white", bd=0, font=("Segoe UI", 10), cursor="hand2", width=12).pack(side="left")
        tk.Button(btns, text="Cancel", command=self.show_main_screen, bg="#444", fg="white", activebackground="#555", activeforeground="white", bd=0, font=("Segoe UI", 10), cursor="hand2", width=12).pack(side="right")
        
        self.root.bind("<Return>", lambda e: self.save_edit(platform, acc['username']))
        self.root.bind("<Escape>", lambda e: self.show_main_screen())
    
    def save_edit(self, platform, username):
        password = self.edit_password.get()
        secretco = self.edit_secretco.get().strip()
        
        if not password and not secretco:
            self.show_message("No changes to save", False)
            return
        
        success, msg = update_credential(platform, username, password, secretco, self.master_key)
        if success:
            self.show_main_screen()
            self.show_message(msg, True)
        else:
            self.show_message(msg, False)
    
    def run(self):
        self.root.mainloop()

def open_credential_editor(parent=None):
    from popup import close_popup
    close_popup()
    return CredentialEditorApp(parent)

if __name__ == "__main__":
    CredentialEditorApp().run()
