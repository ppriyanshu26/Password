import tkinter as tk
from tkinter import ttk
import win32gui
import time
import threading
from credentials import master_key_exists
from config import *
from utils import force_foreground, create_account_frame, verify_and_cache_master_key

class PasswordPopup:
    cached_master_key = None; cached_master_key_time = None
    
    def __init__(self, accounts, on_close=None):
        self.accounts = accounts; self.on_close = on_close; self.root = None; self.selected_index = 0; self.authenticated = False; self.master_entry = None; self.error_label = None; self.account_frames = []; self.check_outside_id = None; self.previous_focus_hwnd = None; self._closing = False; self.pending_callbacks = []
        
    def show(self):
        self.previous_focus_hwnd = win32gui.GetForegroundWindow()
        self.root = tk.Toplevel()
        self.root.title(APP_NAME)
        self.root.attributes("-topmost", True)
        self.root.overrideredirect(True)
        
        # Create a thread-safe close handler
        self.close_event = threading.Event()
        
        x = self.root.winfo_pointerx()
        y = self.root.winfo_pointery()
        
        self.main_frame = tk.Frame(self.root, bg=COLOR_BG_DARK, bd=2, relief="solid")
        self.main_frame.pack(fill="both", expand=True)
        
        header = tk.Label(self.main_frame, text="🔐 Password Manager", font=FONT_HEADER,bg=COLOR_BG_DARKER, fg=COLOR_TEXT_PRIMARY, pady=8)
        header.pack(fill="x")
        
        self._show_master_key_input()
        self.root.bind("<Escape>", self._close)
        self.root.update_idletasks()
        width = WINDOW_WIDTH
        height = WINDOW_HEIGHT
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = max(0, min(x, screen_width - width))
        y = max(0, min(y, screen_height - height))
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        self.root.deiconify()
        self.root.lift()
        self.root.attributes("-topmost", True)
        self.root.focus_force()
        self._check_click_outside()
        self.pending_callbacks.append(self.root.after(10, self._focus_entry))
        self.pending_callbacks.append(self.root.after(50, self._focus_entry))
        self.pending_callbacks.append(self.root.after(100, self._focus_entry))
        self.pending_callbacks.append(self.root.after(200, self._focus_entry))
        
        # Don't call mainloop() - the parent root's mainloop is already running
    
    def _focus_entry(self):
        if not self.root or not self.root.winfo_exists():
            return
        if self.master_entry and self.master_entry.winfo_exists():
            force_foreground(self.root)
            self.root.lift()
            self.root.attributes("-topmost", True)
            self.root.focus_force()
            self.master_entry.focus_set()
            self.master_entry.icursor(tk.END)
    
    def _is_master_key_cached_and_valid(self):
        if PasswordPopup.cached_master_key is None or PasswordPopup.cached_master_key_time is None:
            return False
        elapsed = time.time() - PasswordPopup.cached_master_key_time
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
        label = tk.Label(self.auth_frame, text=prompt_text, font=FONT_LABEL, bg=COLOR_BG_DARK, fg=COLOR_TEXT_PRIMARY)
        label.pack(anchor="w", pady=(0, 5))
        
        self.master_entry = tk.Entry(self.auth_frame, font=FONT_INPUT, show="•", bg=COLOR_BG_MEDIUM, fg=COLOR_TEXT_PRIMARY, insertbackground=COLOR_TEXT_PRIMARY, relief="flat", width=25)
        self.master_entry.pack(fill="x", pady=(0, 10), ipady=8)
        self.master_entry.bind("<Return>", self._verify_master_key)
        
        self.error_label = tk.Label(self.auth_frame, text="", font=FONT_ERROR, bg=COLOR_BG_DARK, fg=COLOR_ERROR)
        self.error_label.pack(anchor="w")
        
        submit_btn = tk.Button(self.auth_frame, text="Unlock" if not is_setup else "Set Key", font=FONT_LABEL, bg=COLOR_ACCENT, fg=COLOR_BG_DARKER, relief="flat", cursor="hand2", command=self._verify_master_key, padx=20, pady=5)
        submit_btn.pack(pady=(10, 0))
        
        hint = tk.Label(self.auth_frame, text="Press Enter to submit • Esc to close", font=FONT_HINT, bg=COLOR_BG_DARK, fg=COLOR_TEXT_MUTED)
        hint.pack(pady=(15, 0))
    
    def _verify_master_key(self, event=None):
        result = verify_and_cache_master_key(self.master_entry.get(), None)
        
        if not result["success"]:
            self.error_label.config(text=result["error"])
            self.master_entry.delete(0, tk.END)
            self.master_entry.focus_set()
            return
        
        PasswordPopup.cached_master_key = result["key"]
        PasswordPopup.cached_master_key_time = time.time()
        self.authenticated = True
        self._show_accounts()
    
    def _show_accounts(self):
        if hasattr(self, 'auth_frame'):
            self.auth_frame.destroy()
        
        content_frame = tk.Frame(self.main_frame, bg=COLOR_BG_DARK)
        content_frame.pack(fill="both", expand=True)
        
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
        
        if not self.accounts and not all_vault_accounts:
            no_acc_label = tk.Label(content_frame, text="No accounts found", font=FONT_LABEL, bg=COLOR_BG_DARK, fg=COLOR_TEXT_SECONDARY, pady=20, padx=40)
            no_acc_label.pack()
        elif not self.accounts:
            no_acc_label = tk.Label(content_frame, text="No accounts found", font=FONT_LABEL, bg=COLOR_BG_DARK, fg=COLOR_TEXT_SECONDARY, pady=10, padx=40)
            no_acc_label.pack()
            
            all_label = tk.Label(content_frame, text="All Accounts:", font=FONT_LABEL, bg=COLOR_BG_DARK, fg=COLOR_TEXT_PRIMARY, pady=5)
            all_label.pack(anchor="w", padx=10)
            
            canvas = tk.Canvas(content_frame, bg=COLOR_BG_DARK, highlightthickness=0)
            scrollbar = ttk.Scrollbar(content_frame, orient="vertical", command=canvas.yview)
            scrollable_frame = tk.Frame(canvas, bg=COLOR_BG_DARK)
            scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
            
            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)
            
            self.account_frames = []
            for idx, account in enumerate(all_vault_accounts):
                frame = create_account_frame(scrollable_frame, account, idx, self._on_account_click, self)
                frame.pack(fill="x", padx=5, pady=2)
                self.account_frames.append(frame)
            
            canvas.pack(side="left", fill="both", expand=True, padx=5, pady=5)
            scrollbar.pack(side="right", fill="y")
            
            self._bind_mousewheel(canvas)
        else:
            canvas = tk.Canvas(content_frame, bg=COLOR_BG_DARK, highlightthickness=0)
            scrollbar = ttk.Scrollbar(content_frame, orient="vertical", command=canvas.yview)
            scrollable_frame = tk.Frame(canvas, bg=COLOR_BG_DARK)
            scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
            
            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)
            
            self.account_frames = []
            matched_accounts = self.accounts[:]
            other_accounts = []
            
            matched_set = {(a["service"], a["username"]) for a in matched_accounts}
            for acc in all_vault_accounts:
                if (acc["service"], acc["username"]) not in matched_set:
                    other_accounts.append(acc)
            
            other_accounts.sort(key=lambda x: (x["service"].lower(), x["username"].lower()))
            
            for idx, account in enumerate(matched_accounts):
                frame = create_account_frame(scrollable_frame, account, idx, self._on_account_click, self)
                frame.pack(fill="x", padx=5, pady=2)
                self.account_frames.append(frame)
            
            if other_accounts:
                for idx, account in enumerate(other_accounts, start=len(matched_accounts)):
                    frame = create_account_frame(scrollable_frame, account, idx, self._on_account_click, self)
                    frame.pack(fill="x", padx=5, pady=2)
                    self.account_frames.append(frame)
            
            canvas.pack(side="left", fill="both", expand=True, padx=5, pady=5)
            scrollbar.pack(side="right", fill="y")
            
            self._bind_mousewheel(canvas)
    
    def _bind_mousewheel(self, canvas):
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
    
    def _on_account_click(self, index):
        self.selected_index = index
    
    def _check_click_outside(self):
        if not self.root or not self.root.winfo_exists() or self._closing:
            return
        
        try:
            x = self.root.winfo_x()
            y = self.root.winfo_y()
            width = self.root.winfo_width()
            height = self.root.winfo_height()
            
            mouse_x = self.root.winfo_pointerx()
            mouse_y = self.root.winfo_pointery()
            
            if mouse_x < x or mouse_x > x + width or mouse_y < y or mouse_y > y + height:
                self.root.after(0, self._close)
                return
        except tk.TclError:
            # Window was destroyed, stop checking
            return
        except Exception as e:
            print(f"Error checking click outside: {e}")
        
        try:
            callback_id = self.root.after(CLICK_OUTSIDE_CHECK_INTERVAL, self._check_click_outside)
            self.check_outside_id = callback_id
            self.pending_callbacks.append(callback_id)
        except tk.TclError:
            # Window was destroyed
            pass
    
    def _close(self, event=None):
        if self._closing or not self.root:
            return
        
        self._closing = True
        
        try:
            # Cancel all pending callbacks before destroying the window
            if self.root.winfo_exists():
                try:
                    if self.check_outside_id:
                        self.root.after_cancel(self.check_outside_id)
                        self.check_outside_id = None
                except tk.TclError:
                    pass
                
                # Cancel all other pending callbacks
                for callback_id in self.pending_callbacks:
                    try:
                        self.root.after_cancel(callback_id)
                    except tk.TclError:
                        pass
                self.pending_callbacks.clear()
                
                # Now destroy the window
                self.root.grab_release()
                self.root.destroy()
            
            self.root = None
            print("[Password Manager] Popup disappeared")
        except tk.TclError:
            # Window already destroyed, ignore
            pass
        except Exception as e:
            print(f"Error closing popup: {e}")
        
        if self.previous_focus_hwnd:
            try:
                win32gui.SetForegroundWindow(self.previous_focus_hwnd)
            except:
                pass
        
        if self.on_close:
            self.on_close()

def show_popup(accounts):
    popup = PasswordPopup(accounts)
    popup.show()
def show_popup_from_root(root, accounts, on_close=None):
    """Show popup using an existing Tkinter root window (main thread safe)"""
    popup = PasswordPopup(accounts, on_close=on_close)
    # Create the popup as a top-level but use the provided root
    popup.parent_root = root
    popup.show()