import tkinter as tk
from tkinter import ttk
import pyotp
import win32gui
import win32con
import win32process
import ctypes
import time
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


class PasswordPopup:
    MASTER_KEY_CACHE_TIMEOUT = 300  # 5 minutes in seconds
    
    def __init__(self, accounts, on_close=None):
        self.accounts = accounts
        self.on_close = on_close
        self.root = None
        self.selected_index = 0
        self.authenticated = False
        self.master_entry = None
        self.error_label = None
        self.account_frames = []
        self.check_outside_id = None
        self.cached_master_key = None
        self.cached_master_key_time = None
        
    def show(self):
        self.root = tk.Tk()
        self.root.title("Password Manager")
        self.root.attributes("-topmost", True)
        self.root.overrideredirect(True)
        
        x = self.root.winfo_pointerx()
        y = self.root.winfo_pointery()
        
        self.main_frame = tk.Frame(self.root, bg="#2b2b2b", bd=2, relief="solid")
        self.main_frame.pack(fill="both", expand=True)
        
        header = tk.Label(
            self.main_frame, 
            text="🔐 Password Manager", 
            font=("Segoe UI", 11, "bold"),
            bg="#1a1a2e", 
            fg="#ffffff",
            pady=8
        )
        header.pack(fill="x")
        
        self._show_master_key_input()
        
        self.root.bind("<Escape>", self._close)
        
        self.root.update_idletasks()
        # Fixed size
        width = 400
        height = 500
        
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        x = min(x, screen_width - width - 10)
        y = min(y, screen_height - height - 50)
        
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        
        self.root.deiconify()
        self.root.lift()
        self.root.attributes("-topmost", True)
        
        self.root.focus_force()
        
        self._check_click_outside()
        
        self.root.after(10, self._focus_entry)
        self.root.after(50, self._focus_entry)
        self.root.after(100, self._focus_entry)
        self.root.after(200, self._focus_entry)
        
        self.root.mainloop()
    
    def _focus_entry(self):
        if self.master_entry and self.master_entry.winfo_exists():
            force_foreground(self.root)
            
            self.root.lift()
            self.root.attributes("-topmost", True)
            self.root.focus_force()
            self.master_entry.focus_set()
            self.master_entry.icursor(tk.END)
    
    def _is_master_key_cached_and_valid(self):
        """Check if master key is cached and still within 5-minute window"""
        if self.cached_master_key is None or self.cached_master_key_time is None:
            return False
        elapsed = time.time() - self.cached_master_key_time
        return elapsed < self.MASTER_KEY_CACHE_TIMEOUT
    
    def _show_master_key_input(self):
        # Check if we have a valid cached master key
        if self._is_master_key_cached_and_valid():
            self.authenticated = True
            self._show_accounts()
            return
        
        self.auth_frame = tk.Frame(self.main_frame, bg="#2b2b2b")
        self.auth_frame.pack(fill="both", expand=True, padx=15, pady=15)
        
        is_setup = not master_key_exists()
        
        prompt_text = "Create Master Key:" if is_setup else "Enter Master Key:"
        label = tk.Label(
            self.auth_frame,
            text=prompt_text,
            font=("Segoe UI", 10),
            bg="#2b2b2b",
            fg="#ffffff"
        )
        label.pack(anchor="w", pady=(0, 5))
        
        self.master_entry = tk.Entry(
            self.auth_frame,
            font=("Segoe UI", 11),
            show="•",
            bg="#3b3b3b",
            fg="#ffffff",
            insertbackground="#ffffff",
            relief="flat",
            width=25
        )
        self.master_entry.pack(fill="x", pady=(0, 10), ipady=8)
        self.master_entry.bind("<Return>", self._verify_master_key)
        
        self.error_label = tk.Label(
            self.auth_frame,
            text="",
            font=("Segoe UI", 9),
            bg="#2b2b2b",
            fg="#ff6b6b"
        )
        self.error_label.pack(anchor="w")
        
        submit_btn = tk.Button(
            self.auth_frame,
            text="Unlock" if not is_setup else "Set Key",
            font=("Segoe UI", 10),
            bg="#4fc3f7",
            fg="#1a1a2e",
            relief="flat",
            cursor="hand2",
            command=self._verify_master_key,
            padx=20,
            pady=5
        )
        submit_btn.pack(pady=(10, 0))
        
        hint = tk.Label(
            self.auth_frame,
            text="Press Enter to submit • Esc to close",
            font=("Segoe UI", 8),
            bg="#2b2b2b",
            fg="#666666"
        )
        hint.pack(pady=(15, 0))
    
    def _verify_master_key(self, event=None):
        key = self.master_entry.get()
        
        if not key:
            self.error_label.config(text="Please enter a master key")
            return
        
        if not master_key_exists():
            if len(key) < 4:
                self.error_label.config(text="Key must be at least 4 characters")
                return
            save_master_key(key)
            self.cached_master_key = key
            self.cached_master_key_time = time.time()
            self.authenticated = True
            self._show_accounts()
            return
        
        if verify_master_key(key):
            self.cached_master_key = key
            self.cached_master_key_time = time.time()
            self.authenticated = True
            self._show_accounts()
        else:
            self.error_label.config(text="Invalid master key")
            self.master_entry.delete(0, tk.END)
            self.master_entry.focus_set()
    
    def _show_accounts(self):
        self.auth_frame.destroy()
        
        content_frame = tk.Frame(self.main_frame, bg="#2b2b2b")
        content_frame.pack(fill="both", expand=True)
        
        if not self.accounts:
            no_acc_label = tk.Label(
                content_frame,
                text="No accounts found",
                font=("Segoe UI", 10),
                bg="#2b2b2b",
                fg="#888888",
                pady=20,
                padx=40
            )
            no_acc_label.pack()
        else:
            canvas = tk.Canvas(content_frame, bg="#2b2b2b", highlightthickness=0)
            scrollbar = ttk.Scrollbar(content_frame, orient="vertical", command=canvas.yview)
            scrollable_frame = tk.Frame(canvas, bg="#2b2b2b")
            
            scrollable_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )
            
            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)
            
            self.account_frames = []
            
            # Separate matched accounts from others
            matched_accounts = self.accounts[:]  # All matched accounts from matcher
            other_accounts = []
            
            # Load all accounts from vault to find non-matched ones
            from credentials import load_vault
            all_vault_accounts = []
            try:
                vault = load_vault()
                for service, accounts in vault.items():
                    for account in accounts:
                        all_vault_accounts.append({
                            "service": service,
                            "username": account.get("username", ""),
                            "password": account.get("password", ""),
                            "mfa": account.get("mfa", "")
                        })
            except:
                all_vault_accounts = []
            
            # Find accounts not in matched list
            matched_set = {(a["service"], a["username"]) for a in matched_accounts}
            for acc in all_vault_accounts:
                if (acc["service"], acc["username"]) not in matched_set:
                    other_accounts.append(acc)
            
            # Sort other accounts alphabetically
            other_accounts.sort(key=lambda x: (x["service"].lower(), x["username"].lower()))
            
            # Display matched accounts
            for idx, account in enumerate(matched_accounts):
                frame = self._create_account_frame(scrollable_frame, account, idx)
                frame.pack(fill="x", padx=5, pady=2)
                self.account_frames.append(frame)
            
            # Add divider if there are other accounts
            if other_accounts:
                divider = tk.Frame(scrollable_frame, bg="#4a4a6a", height=2)
                divider.pack(fill="x", padx=5, pady=8)
                
                # Display other accounts alphabetically
                for idx, account in enumerate(other_accounts, start=len(matched_accounts)):
                    frame = self._create_account_frame(scrollable_frame, account, idx)
                    frame.pack(fill="x", padx=5, pady=2)
                    self.account_frames.append(frame)
            
            if self.account_frames:
                self._highlight_item(0)
            
            canvas.pack(side="left", fill="both", expand=True, padx=5, pady=5)
            scrollbar.pack(side="right", fill="y")
        
        footer = tk.Label(
            self.main_frame,
            text="↑↓ Navigate • Enter: Password • Tab: Username • M: MFA • Esc: Close",
            font=("Segoe UI", 8),
            bg="#1a1a2e",
            fg="#888888",
            pady=5
        )
        footer.pack(fill="x")
        
        self.root.bind("<Return>", self._copy_password)
        self.root.bind("<Tab>", self._copy_username)
        self.root.bind("<m>", self._copy_mfa)
        self.root.bind("<M>", self._copy_mfa)
        self.root.bind("<Up>", self._navigate_up)
        self.root.bind("<Down>", self._navigate_down)
        
        self.root.update_idletasks()
        
        current_geom = self.root.geometry()
        pos = current_geom.split('+')[1:]
        x, y = int(pos[0]), int(pos[1])
        
        self.root.geometry(f"400x500+{x}+{y}")
    
    def _create_account_frame(self, parent, account, idx):
        frame = tk.Frame(parent, bg="#3b3b3b", cursor="hand2")
        frame.account_data = account
        frame.index = idx
        
        service_label = tk.Label(
            frame,
            text=f"🌐 {account['service']}",
            font=("Segoe UI", 10, "bold"),
            bg="#3b3b3b",
            fg="#4fc3f7",
            anchor="w"
        )
        service_label.pack(fill="x", padx=10, pady=(8, 2))
        
        username_label = tk.Label(
            frame,
            text=f"👤 {account['username']}",
            font=("Segoe UI", 9),
            bg="#3b3b3b",
            fg="#ffffff",
            anchor="w"
        )
        username_label.pack(fill="x", padx=10, pady=(0, 8))
        
        frame.bind("<Button-1>", lambda e, i=idx: self._select_and_copy_password(i))
        service_label.bind("<Button-1>", lambda e, i=idx: self._select_and_copy_password(i))
        username_label.bind("<Button-1>", lambda e, i=idx: self._select_and_copy_password(i))
        
        return frame
    
    def _highlight_item(self, index):
        for i, frame in enumerate(self.account_frames):
            if i == index:
                frame.configure(bg="#4a4a6a")
                for child in frame.winfo_children():
                    child.configure(bg="#4a4a6a")
            else:
                frame.configure(bg="#3b3b3b")
                for child in frame.winfo_children():
                    child.configure(bg="#3b3b3b")
    
    def _navigate_up(self, event=None):
        if self.accounts and self.selected_index > 0:
            self.selected_index -= 1
            self._highlight_item(self.selected_index)
    
    def _navigate_down(self, event=None):
        if self.accounts and self.selected_index < len(self.accounts) - 1:
            self.selected_index += 1
            self._highlight_item(self.selected_index)
    
    def _select_and_copy_password(self, index):
        self.selected_index = index
        self._highlight_item(index)
        self._copy_password()
    
    def _copy_password(self, event=None):
        if not self.authenticated:
            return
        if self.accounts:
            password = self.accounts[self.selected_index]["password"]
            print(f"Password: {password}")
            self._show_toast("Password printed to console!")
            self._close()
    
    def _copy_username(self, event=None):
        if not self.authenticated:
            return "break"
        if self.accounts:
            username = self.accounts[self.selected_index]["username"]
            print(f"Username: {username}")
            self._show_toast("Username printed to console!")
            self._close()
        return "break"
    
    def _copy_mfa(self, event=None):
        if not self.authenticated:
            return
        if self.accounts:
            mfa_secret = self.accounts[self.selected_index].get("mfa", "")
            if mfa_secret:
                try:
                    totp = pyotp.TOTP(mfa_secret)
                    code = totp.now()
                    print(f"MFA Code: {code}")
                    self._show_toast(f"MFA code printed to console: {code}")
                except Exception as e:
                    self._show_toast("Invalid MFA secret")
                    return
            else:
                self._show_toast("No MFA configured")
                return
            self._close()
    
    def _show_toast(self, message):
        print(f"[Password Manager] {message}")
    
    def _check_click_outside(self):
        """Check if mouse is outside and close if it is"""
        if not self.root or not self.root.winfo_exists():
            return
        
        try:
            x = self.root.winfo_x()
            y = self.root.winfo_y()
            width = self.root.winfo_width()
            height = self.root.winfo_height()
            
            mouse_x = self.root.winfo_pointerx()
            mouse_y = self.root.winfo_pointery()
            
            # Check if mouse is outside the window
            if mouse_x < x or mouse_x > x + width or mouse_y < y or mouse_y > y + height:
                self._close()
                return
        except:
            pass
        
        # Schedule next check
        self.check_outside_id = self.root.after(100, self._check_click_outside)
    
    def _close(self, event=None):
        if self.root:
            if self.check_outside_id:
                self.root.after_cancel(self.check_outside_id)
                self.check_outside_id = None
            self.root.grab_release()
            self.root.destroy()
            self.root = None
            print("[Password Manager] Popup disappeared")
        if self.on_close:
            self.on_close()


def show_popup(accounts):
    popup = PasswordPopup(accounts)
    popup.show()
