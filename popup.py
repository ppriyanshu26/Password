import tkinter as tk
from tkinter import ttk
import pyotp
import win32gui
import time
from credentials import verify_master_key, master_key_exists, save_master_key
from config import (
    MASTER_KEY_CACHE_TIMEOUT,
    COLOR_BG_DARK, COLOR_BG_DARKER, COLOR_BG_MEDIUM, COLOR_BG_HIGHLIGHT,
    COLOR_ACCENT, COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_TEXT_MUTED,
    COLOR_ERROR, COLOR_BORDER,
    WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_PADDING_X, WINDOW_PADDING_Y,
    CLICK_OUTSIDE_CHECK_INTERVAL,
    FONT_HEADER, FONT_LABEL, FONT_INPUT, FONT_ACCOUNT_SERVICE,
    FONT_ACCOUNT_USERNAME, FONT_FOOTER, FONT_ERROR, FONT_HINT,
    APP_NAME
)
from utils import force_foreground, create_account_frame, highlight_items, show_toast


class PasswordPopup:
    
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
        self.previous_focus_hwnd = None
        
    def show(self):
        self.previous_focus_hwnd = win32gui.GetForegroundWindow()
        
        self.root = tk.Tk()
        self.root.title(APP_NAME)
        self.root.attributes("-topmost", True)
        self.root.overrideredirect(True)
        
        x = self.root.winfo_pointerx()
        y = self.root.winfo_pointery()
        
        self.main_frame = tk.Frame(self.root, bg=COLOR_BG_DARK, bd=2, relief="solid")
        self.main_frame.pack(fill="both", expand=True)
        
        header = tk.Label(
            self.main_frame, 
            text="🔐 Password Manager", 
            font=FONT_HEADER,
            bg=COLOR_BG_DARKER, 
            fg=COLOR_TEXT_PRIMARY,
            pady=8
        )
        header.pack(fill="x")
        
        self._show_master_key_input()
        
        self.root.bind("<Escape>", self._close)
        
        self.root.update_idletasks()
        width = WINDOW_WIDTH
        height = WINDOW_HEIGHT
        
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
        if self.cached_master_key is None or self.cached_master_key_time is None:
            return False
        elapsed = time.time() - self.cached_master_key_time
        return elapsed < MASTER_KEY_CACHE_TIMEOUT
    
    def _show_master_key_input(self):
        if self._is_master_key_cached_and_valid():
            self.authenticated = True
            self._show_accounts()
            return
        
        self.auth_frame = tk.Frame(self.main_frame, bg=COLOR_BG_DARK)
        self.auth_frame.pack(fill="both", expand=True, padx=WINDOW_PADDING_X, pady=WINDOW_PADDING_Y)
        
        is_setup = not master_key_exists()
        
        prompt_text = "Create Master Key:" if is_setup else "Enter Master Key:"
        label = tk.Label(
            self.auth_frame,
            text=prompt_text,
            font=FONT_LABEL,
            bg=COLOR_BG_DARK,
            fg=COLOR_TEXT_PRIMARY
        )
        label.pack(anchor="w", pady=(0, 5))
        
        self.master_entry = tk.Entry(
            self.auth_frame,
            font=FONT_INPUT,
            show="•",
            bg=COLOR_BG_MEDIUM,
            fg=COLOR_TEXT_PRIMARY,
            insertbackground=COLOR_TEXT_PRIMARY,
            relief="flat",
            width=25
        )
        self.master_entry.pack(fill="x", pady=(0, 10), ipady=8)
        self.master_entry.bind("<Return>", self._verify_master_key)
        
        self.error_label = tk.Label(
            self.auth_frame,
            text="",
            font=FONT_ERROR,
            bg=COLOR_BG_DARK,
            fg=COLOR_ERROR
        )
        self.error_label.pack(anchor="w")
        
        submit_btn = tk.Button(
            self.auth_frame,
            text="Unlock" if not is_setup else "Set Key",
            font=FONT_LABEL,
            bg=COLOR_ACCENT,
            fg=COLOR_BG_DARKER,
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
            font=FONT_HINT,
            bg=COLOR_BG_DARK,
            fg=COLOR_TEXT_MUTED
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
        
        content_frame = tk.Frame(self.main_frame, bg=COLOR_BG_DARK)
        content_frame.pack(fill="both", expand=True)
        
        if not self.accounts:
            no_acc_label = tk.Label(
                content_frame,
                text="No accounts found",
                font=FONT_LABEL,
                bg=COLOR_BG_DARK,
                fg=COLOR_TEXT_SECONDARY,
                pady=20,
                padx=40
            )
            no_acc_label.pack()
        else:
            canvas = tk.Canvas(content_frame, bg=COLOR_BG_DARK, highlightthickness=0)
            scrollbar = ttk.Scrollbar(content_frame, orient="vertical", command=canvas.yview)
            scrollable_frame = tk.Frame(canvas, bg=COLOR_BG_DARK)
            
            scrollable_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )
            
            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)
            
            self.account_frames = []
            
            matched_accounts = self.accounts[:]
            other_accounts = []
            
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
            
            matched_set = {(a["service"], a["username"]) for a in matched_accounts}
            for acc in all_vault_accounts:
                if (acc["service"], acc["username"]) not in matched_set:
                    other_accounts.append(acc)
            
            other_accounts.sort(key=lambda x: (x["service"].lower(), x["username"].lower()))
            
            for idx, account in enumerate(matched_accounts):
                frame = create_account_frame(scrollable_frame, account, idx, self._select_and_copy_password)
                frame.pack(fill="x", padx=5, pady=2)
                self.account_frames.append(frame)
            
            if other_accounts:
                divider = tk.Frame(scrollable_frame, bg=COLOR_BG_HIGHLIGHT, height=2)
                divider.pack(fill="x", padx=5, pady=8)
                
                for idx, account in enumerate(other_accounts, start=len(matched_accounts)):
                    frame = create_account_frame(scrollable_frame, account, idx, self._select_and_copy_password)
                    frame.pack(fill="x", padx=5, pady=2)
                    self.account_frames.append(frame)
            
            if self.account_frames:
                highlight_items(self.account_frames, 0)
            
            canvas.pack(side="left", fill="both", expand=True, padx=5, pady=5)
            scrollbar.pack(side="right", fill="y")
        
        footer = tk.Label(
            self.main_frame,
            text="↑↓ Navigate • Enter: Password • Tab: Username • M: MFA • Esc: Close",
            font=FONT_FOOTER,
            bg=COLOR_BG_DARKER,
            fg=COLOR_TEXT_SECONDARY,
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
        
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}+{x}+{y}")
    
    def _navigate_up(self, event=None):
        if self.accounts and self.selected_index > 0:
            self.selected_index -= 1
            highlight_items(self.account_frames, self.selected_index)
    
    def _navigate_down(self, event=None):
        if self.accounts and self.selected_index < len(self.accounts) - 1:
            self.selected_index += 1
            highlight_items(self.account_frames, self.selected_index)
    
    def _select_and_copy_password(self, index):
        self.selected_index = index
        highlight_items(self.account_frames, index)
        self._copy_password()
    
    def _copy_password(self, event=None):
        if not self.authenticated:
            return
        if self.accounts:
            password = self.accounts[self.selected_index]["password"]
            print(f"Password: {password}")
            show_toast("Password printed to console!")
            self._close()
    
    def _copy_username(self, event=None):
        if not self.authenticated:
            return "break"
        if self.accounts:
            username = self.accounts[self.selected_index]["username"]
            print(f"Username: {username}")
            show_toast("Username printed to console!")
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
                    show_toast(f"MFA code printed to console: {code}")
                except Exception as e:
                    show_toast("Invalid MFA secret")
                    return
            else:
                show_toast("No MFA configured")
                return
            self._close()
    
    def _check_click_outside(self):
        if not self.root or not self.root.winfo_exists():
            return
        
        try:
            x = self.root.winfo_x()
            y = self.root.winfo_y()
            width = self.root.winfo_width()
            height = self.root.winfo_height()
            
            mouse_x = self.root.winfo_pointerx()
            mouse_y = self.root.winfo_pointery()
            
            if mouse_x < x or mouse_x > x + width or mouse_y < y or mouse_y > y + height:
                self._close()
                return
        except:
            pass
        
        self.check_outside_id = self.root.after(CLICK_OUTSIDE_CHECK_INTERVAL, self._check_click_outside)
    
    def _close(self, event=None):
        if self.root:
            if self.check_outside_id:
                self.root.after_cancel(self.check_outside_id)
                self.check_outside_id = None
            self.root.grab_release()
            self.root.destroy()
            self.root = None
            print("[Password Manager] Popup disappeared")
        
        if self.previous_focus_hwnd:
            try:
                win32gui.SetForegroundWindow(self.previous_focus_hwnd)
            except Exception as e:
                print(f"Could not restore focus: {e}")
        
        if self.on_close:
            self.on_close()


def show_popup(accounts):
    popup = PasswordPopup(accounts)
    popup.show()
