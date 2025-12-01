import time
import tkinter as tk
from tkinter import ttk
import keyboard
import win32gui
import win32con
import win32api
from crypto import Crypto
from functions import generate_totp, load_creds, add_credential, delete_credential, download

class PasswordFillerGUI:
    APP_COLOR = '#F7DC6F'; BUTTON_COLOR = '#00CED1' 
    def __init__(self, ver):
        self.root = None; self.credentials = load_creds(); self.crypto = None; self.VERSION = ver; self.create_window()
        
    def create_window(self):
        if self.root is not None:
            try:
                self.root.destroy()
            except:
                pass
        self.root = tk.Tk()
        self.root.title(f"Password Filler v{self.VERSION}")
        self.root.resizable(False, False)
        self.root.attributes('-topmost', True)
        self.root.configure(bg='#1a1a2e')
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
        style.configure('TFrame', background='#1a1a2e')
        style.configure('TLabel', background='#1a1a2e', foreground='#eaeaea', font=('Segoe UI', 10))
        style.configure('Title.TLabel', font=('Segoe UI', 12, 'bold'), foreground='#4ECDC4')
        style.configure('TButton', font=('Segoe UI', 9), background='#16213e', foreground='white')
        style.map('TButton', background=[('active', '#0f3460')])
        style.configure('Error.TLabel', background='#1a1a2e', foreground='#ff6b6b', font=('Segoe UI', 9))
        style.configure('Success.TLabel', background='#1a1a2e', foreground='#4ECDC4', font=('Segoe UI', 9))
        
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
        
        ttk.Label(key_frame, text="Encryption Key:", foreground=self.APP_COLOR).pack(anchor=tk.W)
        
        self.key_entry = tk.Entry(key_frame, show="•", font=('Segoe UI', 11), bg='#16213e', fg=self.APP_COLOR, insertbackground=self.APP_COLOR,relief='flat', highlightthickness=2, highlightcolor=self.APP_COLOR,highlightbackground='#0f3460')
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
    
    def _get_color_for_app(self, index):
        return self.APP_COLOR
    
    def show_main_content(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        
        self.root.bind('<Escape>', lambda e: self.lock())
        self.root.bind('<Return>', lambda e: self.fill_creds())
        
        ttk.Label(self.main_frame, text="🔑 Password Filler", style='Title.TLabel').pack(pady=(0, 10))
        
        content_frame = ttk.Frame(self.main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        self.apps_frame = ttk.Frame(content_frame, width=120)
        self.apps_frame.pack(side=tk.LEFT, fill=tk.Y, expand=True, padx=(0, 5))
        self.apps_frame.pack_propagate(False)
        apps_label = ttk.Label(self.apps_frame, text="📱 Apps", font=('Segoe UI', 12, 'bold'), foreground=self.APP_COLOR)
        apps_label.pack(anchor=tk.W, pady=(0, 5))
        apps_canvas = tk.Canvas(self.apps_frame, bg='#1a1a2e', highlightthickness=0)
        apps_scrollbar = ttk.Scrollbar(self.apps_frame, orient="vertical", command=apps_canvas.yview)
        self.apps_inner_frame = ttk.Frame(apps_canvas)
        self.apps_inner_frame.bind("<Configure>", lambda e: apps_canvas.configure(scrollregion=apps_canvas.bbox("all")))
        apps_canvas.create_window((0, 0), window=self.apps_inner_frame, anchor="nw")
        apps_canvas.configure(yscrollcommand=apps_scrollbar.set)
        apps_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        apps_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.apps_canvas = apps_canvas
        def _on_apps_mousewheel(event):
            apps_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        apps_canvas.bind("<MouseWheel>", _on_apps_mousewheel)
        self.apps_inner_frame.bind("<MouseWheel>", _on_apps_mousewheel)
        
        self.users_frame = ttk.Frame(content_frame, width=180)
        self.selected_app = None
        self.selected_app_btn = None
        self.app_buttons = {}
        self.app_colors = {}
        self.matched_creds = []
        
        for idx, app in enumerate(self.credentials.keys()):
            color = self._get_color_for_app(idx)
            self.app_colors[app] = color
        
            app_btn = tk.Button(self.apps_inner_frame,text=app.upper(),font=('Segoe UI', 10, 'bold'),bg='#16213e',fg=color,activebackground=color,activeforeground='#1a1a2e',relief='flat',cursor='hand2',padx=8,pady=8,width=10,anchor='center',highlightthickness=3,highlightbackground=color,highlightcolor=color,bd=0)
            app_btn.pack(fill=tk.X, pady=3, padx=2)
            app_btn.bind('<Enter>', lambda e, b=app_btn, c=color: self._on_app_hover(b, True, c))
            app_btn.bind('<Leave>', lambda e, b=app_btn, c=color: self._on_app_hover(b, False, c))
            app_btn.bind('<MouseWheel>', _on_apps_mousewheel)
            app_btn.configure(command=lambda a=app, b=app_btn: self._select_app(a, b))
            self.app_buttons[app] = app_btn
        btn_frame = ttk.Frame(self.main_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        
        for i in range(4):
            btn_frame.columnconfigure(i, weight=1)
        
        fill_btn = tk.Button(btn_frame, text="📝 Fill Creds", command=self.fill_creds,bg=self.BUTTON_COLOR, fg='#1a1a2e', font=('Segoe UI', 9, 'bold'),relief='flat', cursor='hand2', width=10, pady=4)
        fill_btn.grid(row=0, column=0, padx=2, sticky='ew')
        
        totp_btn = tk.Button(btn_frame, text="🔢 Fill TOTP", command=self.fill_totp,bg=self.BUTTON_COLOR, fg='#1a1a2e', font=('Segoe UI', 9, 'bold'),relief='flat', cursor='hand2', width=10, pady=4)
        totp_btn.grid(row=0, column=1, padx=2, sticky='ew')
        
        edit_btn = tk.Button(btn_frame, text="✏️ Edit", command=self.edit_creds,bg=self.BUTTON_COLOR, fg='#1a1a2e', font=('Segoe UI', 9, 'bold'),relief='flat', cursor='hand2', width=10, pady=4)
        edit_btn.grid(row=0, column=2, padx=2, sticky='ew')
        
        downloads_btn = tk.Button(btn_frame, text="📥 Downloads", command=self.download_excel,bg=self.BUTTON_COLOR, fg='#1a1a2e', font=('Segoe UI', 9, 'bold'),relief='flat', cursor='hand2', width=10, pady=4)
        downloads_btn.grid(row=0, column=3, padx=2, sticky='ew')
        
        self.message_label = ttk.Label(self.main_frame, text="", style='Error.TLabel')
        self.message_label.pack(pady=(5, 0))
    
    def _on_app_hover(self, btn, entering, color):
        if btn != self.selected_app_btn:
            if entering:
                btn.configure(bg=color, fg='#1a1a2e')
            else:
                btn.configure(bg='#16213e', fg=color)
    
    def _select_app(self, app, btn):
        if self.selected_app_btn:
            old_color = self.app_colors.get(self.selected_app, '#4ECDC4')
            self.selected_app_btn.configure(bg='#16213e', fg=old_color)
        
        self.selected_app = app
        self.selected_app_btn = btn
        color = self.app_colors.get(app, '#4ECDC4')
        btn.configure(bg=color, fg='#1a1a2e')
        self.users_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(5, 0))
        for widget in self.users_frame.winfo_children():
            widget.destroy()
        header_frame = ttk.Frame(self.users_frame)
        header_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(header_frame, text=f"👤 Users", font=('Segoe UI', 12, 'bold'),foreground=color).pack(side=tk.LEFT)
        
        close_btn = tk.Button(header_frame, text="✕", font=('Segoe UI', 14, 'bold'),bg='#1a1a2e', fg='#FF3333', activebackground='#FF3333', activeforeground='white',relief='flat', cursor='hand2', padx=5)
        close_btn.pack(side=tk.RIGHT)
        close_btn.bind('<Button-1>', lambda e: self._close_users_panel())
        
        users_list_frame = ttk.Frame(self.users_frame)
        users_list_frame.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(users_list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.cred_listbox = tk.Listbox(users_list_frame,yscrollcommand=scrollbar.set,bg='#16213e',fg='#eaeaea',selectbackground=color,selectforeground='#1a1a2e',font=('Segoe UI', 10),relief='flat',highlightthickness=2,highlightbackground=color,highlightcolor=color)
        self.cred_listbox.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.cred_listbox.yview)
        
        def _on_users_mousewheel(event):
            self.cred_listbox.yview_scroll(int(-1*(event.delta/120)), "units")
        self.cred_listbox.bind("<MouseWheel>", _on_users_mousewheel)
        
        self.matched_creds = []
        for cred in self.credentials.get(app, []):
            self.matched_creds.append((app, cred))
            self.cred_listbox.insert(tk.END, cred['username'])
        
        if self.matched_creds:
            self.cred_listbox.selection_set(0)
        
        self.cred_listbox.focus_set()
    
    def _close_users_panel(self):
        self.users_frame.pack_forget()
        if self.selected_app_btn:
            old_color = self.app_colors.get(self.selected_app, '#4ECDC4')
            self.selected_app_btn.configure(bg='#16213e', fg=old_color)
        self.selected_app = None
        self.selected_app_btn = None
        self.matched_creds = []
        
        if hasattr(self, 'cred_listbox'):
            self.cred_listbox.focus_set()
    
    def get_selected_cred(self):
        if not hasattr(self, 'cred_listbox') or not self.matched_creds:
            self.show_inline_message("Please select an app and username first!", is_error=True)
            return None
        selection = self.cred_listbox.curselection()
        if not selection:
            self.show_inline_message("Please select a credential!", is_error=True)
            return None
        idx = selection[0]
        if idx < len(self.matched_creds):
            return self.matched_creds[idx]
        return None
    
    def fill_creds(self):
        cred = self.get_selected_cred()
        if cred:
            decrypted_password = self.crypto.decrypt_aes256(cred[1]['password'])
            self.close_window()
            time.sleep(0.5)
            keyboard.write(cred[1]['username'])
            keyboard.press_and_release('tab')
            time.sleep(0.1)
            keyboard.write(decrypted_password)
    
    def fill_totp(self):
        cred = self.get_selected_cred()
        if cred:
            secret = cred[1].get('secretco')
            if secret:
                code, _ = generate_totp(self.crypto.decrypt_aes256(secret))
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
        
        ttk.Label(self.main_frame, text="✏️ Edit Credentials", style='Title.TLabel').pack(pady=(0, 10))
        
        dropdown_frame = ttk.Frame(self.main_frame)
        dropdown_frame.pack(fill=tk.X, pady=5, padx=10)
        
        ttk.Label(dropdown_frame, text="📱 Select App:", foreground=self.APP_COLOR, font=('Segoe UI', 10, 'bold')).pack(side=tk.LEFT, padx=(0, 10))
        
        style = ttk.Style()
        style.configure('App.TCombobox', fieldbackground='#16213e',background=self.BUTTON_COLOR,foreground='#eaeaea',arrowcolor=self.APP_COLOR)
        style.map('App.TCombobox',fieldbackground=[('readonly', '#16213e')],selectbackground=[('readonly', self.APP_COLOR)],selectforeground=[('readonly', '#1a1a2e')])
        
        app_names = [app.upper() for app in self.credentials.keys()]
        self.edit_app_var = tk.StringVar()
        
        self.app_dropdown = ttk.Combobox(dropdown_frame, textvariable=self.edit_app_var,values=app_names, state='readonly',font=('Segoe UI', 12, 'bold'), width=25,style='App.TCombobox')
        self.app_dropdown.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.app_dropdown.bind('<<ComboboxSelected>>', self._on_edit_app_selected)
        
        list_frame = ttk.Frame(self.main_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=10, padx=10)
        
        ttk.Label(list_frame, text="👤 Users:", foreground=self.APP_COLOR,font=('Segoe UI', 10, 'bold')).pack(anchor=tk.W, pady=(0, 5))
        
        list_inner_frame = ttk.Frame(list_frame)
        list_inner_frame.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(list_inner_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.cred_listbox = tk.Listbox(list_inner_frame, yscrollcommand=scrollbar.set, bg='#16213e', fg='#eaeaea', selectbackground=self.APP_COLOR,selectforeground='#1a1a2e',font=('Segoe UI', 10),highlightthickness=2,highlightbackground=self.APP_COLOR,highlightcolor=self.APP_COLOR)
        self.cred_listbox.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.cred_listbox.yview)
        
        self.cred_listbox.bind("<MouseWheel>", lambda e: self.cred_listbox.yview_scroll(int(-1*(e.delta/120)), "units"))
        
        self.matched_creds = []
        
        if app_names:
            self.app_dropdown.current(0)
            self._on_edit_app_selected(None)
        
        btn_frame = ttk.Frame(self.main_frame)
        btn_frame.pack(fill=tk.X, pady=5, padx=10)
        
        add_btn = tk.Button(btn_frame, text="➕ Add New", command=self.show_add_form,bg=self.BUTTON_COLOR, fg='#1a1a2e', font=('Segoe UI', 9, 'bold'),relief='flat', cursor='hand2', width=10, pady=4)
        add_btn.pack(side=tk.LEFT, padx=2)
        
        del_btn = tk.Button(btn_frame, text="🗑️ Delete", command=self.confirm_delete,bg=self.BUTTON_COLOR, fg='#1a1a2e', font=('Segoe UI', 9, 'bold'),relief='flat', cursor='hand2', width=10, pady=4)
        del_btn.pack(side=tk.LEFT, padx=2)
        
        back_btn = tk.Button(btn_frame, text="⬅️ Back", command=self.show_main_content,bg=self.BUTTON_COLOR, fg='#1a1a2e', font=('Segoe UI', 9, 'bold'),relief='flat', cursor='hand2', width=10, pady=4)
        back_btn.pack(side=tk.RIGHT, padx=2)
        
        self.message_label = ttk.Label(self.main_frame, text="", style='Error.TLabel')
        self.message_label.pack(pady=(5, 0))
    
    def _on_edit_app_selected(self, event):
        selected_app = self.edit_app_var.get()
        
        self.cred_listbox.delete(0, tk.END)
        self.matched_creds = []
        original_app = None
        for app in self.credentials.keys():
            if app.upper() == selected_app:
                original_app = app
                break
        
        if original_app and original_app in self.credentials:
            for cred in self.credentials[original_app]:
                self.matched_creds.append((original_app, cred))
                self.cred_listbox.insert(tk.END, cred['username'])
        
        if self.matched_creds:
            self.cred_listbox.selection_set(0)
    
    def show_add_form(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        
        self.root.bind('<Escape>', lambda e: self.edit_creds())
        self.root.bind('<Return>', lambda e: self.save_new_credential())
        
        ttk.Label(self.main_frame, text="➕ Add Credential", style='Title.TLabel').pack(pady=(0, 10))
        
        form_frame = ttk.Frame(self.main_frame)
        form_frame.pack(fill=tk.X, pady=5, padx=20)
        
        ttk.Label(form_frame, text="App Name:", foreground=self.APP_COLOR).pack(anchor=tk.W)
        self.app_entry = tk.Entry(form_frame, font=('Segoe UI', 10), bg='#16213e', fg='#eaeaea', insertbackground=self.APP_COLOR, relief='flat',highlightthickness=2, highlightbackground=self.APP_COLOR, highlightcolor=self.APP_COLOR)
        self.app_entry.pack(fill=tk.X, pady=(2, 8), ipady=4)
        
        ttk.Label(form_frame, text="Username:", foreground=self.APP_COLOR).pack(anchor=tk.W)
        self.username_entry = tk.Entry(form_frame, font=('Segoe UI', 10), bg='#16213e', fg='#eaeaea', insertbackground=self.APP_COLOR, relief='flat',highlightthickness=2, highlightbackground=self.APP_COLOR, highlightcolor=self.APP_COLOR)
        self.username_entry.pack(fill=tk.X, pady=(2, 8), ipady=4)
        
        ttk.Label(form_frame, text="Password:", foreground=self.APP_COLOR).pack(anchor=tk.W)
        self.password_entry = tk.Entry(form_frame, show="•", font=('Segoe UI', 10), bg='#16213e', fg='#eaeaea', insertbackground=self.APP_COLOR, relief='flat',highlightthickness=2, highlightbackground=self.APP_COLOR, highlightcolor=self.APP_COLOR)
        self.password_entry.pack(fill=tk.X, pady=(2, 8), ipady=4)
        
        ttk.Label(form_frame, text="TOTP Secret (optional):", foreground=self.APP_COLOR).pack(anchor=tk.W)
        self.secret_entry = tk.Entry(form_frame, font=('Segoe UI', 10), bg='#16213e', fg='#eaeaea', insertbackground=self.APP_COLOR, relief='flat',highlightthickness=2, highlightbackground=self.APP_COLOR, highlightcolor=self.APP_COLOR)
        self.secret_entry.pack(fill=tk.X, pady=(2, 8), ipady=4)
        
        btn_frame = ttk.Frame(self.main_frame)
        btn_frame.pack(fill=tk.X, pady=10, padx=20)
        
        save_btn = tk.Button(btn_frame, text="💾 Save", command=self.save_new_credential,bg=self.BUTTON_COLOR, fg='#1a1a2e', font=('Segoe UI', 9, 'bold'),relief='flat', cursor='hand2', width=10, pady=4)
        save_btn.pack(side=tk.LEFT, padx=2)
        
        cancel_btn = tk.Button(btn_frame, text="❌ Cancel", command=self.edit_creds,bg=self.BUTTON_COLOR, fg='#1a1a2e', font=('Segoe UI', 9, 'bold'),relief='flat', cursor='hand2', width=10, pady=4)
        cancel_btn.pack(side=tk.LEFT, padx=2)
        
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

        ttk.Label(self.main_frame, text="⚠️ Confirm Delete", style='Title.TLabel', 
                  foreground='#FF6B6B').pack(pady=(30, 20))
        
        app, cred_data = cred
        ttk.Label(self.main_frame, text=f"Are you sure you want to delete:").pack(pady=5)
        ttk.Label(self.main_frame, text=f"{app.capitalize()} -> {cred_data['username']}", font=('Consolas', 12, 'bold'), foreground=self.APP_COLOR).pack(pady=10)
        
        btn_frame = ttk.Frame(self.main_frame)
        btn_frame.pack(pady=20)
        
        yes_btn = tk.Button(btn_frame, text="🗑️ Yes, Delete", command=lambda: self.delete_selected(app, cred_data['username']),bg=self.BUTTON_COLOR, fg='#1a1a2e', font=('Segoe UI', 9, 'bold'),relief='flat', cursor='hand2', width=15, pady=4)
        yes_btn.pack(side=tk.LEFT, padx=10)
        
        no_btn = tk.Button(btn_frame, text="❌ Cancel", command=self.edit_creds,bg=self.BUTTON_COLOR, fg='#1a1a2e', font=('Segoe UI', 9, 'bold'),relief='flat', cursor='hand2', width=15, pady=4)
        no_btn.pack(side=tk.LEFT, padx=10)
        
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
    
    def lock(self):
        self.crypto = None
        self.show_lock_screen()
    
    def show_inline_message(self, message, is_error=True, duration=3000):
        if hasattr(self, 'message_label'):
            color = '#ff6b6b' if is_error else self.APP_COLOR
            self.message_label.config(text=message, foreground=color)
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

    def download_excel(self):
        success, message = download(self.crypto)
        self.show_inline_message(message, is_error=not success)
    
PasswordFillerGUI("1.0.0")