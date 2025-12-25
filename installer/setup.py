import os, zipfile, requests, hashlib, keyring, getpass, shutil, subprocess, time, sys
import tkinter as tk
from tkinter import ttk, messagebox
import win32com.client

# ================= CONFIG =================
APP_NAME = "Password-Manager"
SERVICE_NAME = "Password Manager"
ZIP_URL = "https://github.com/ppriyanshu26/Password/releases/download/v1.0.0/wow.zip"
EXPECTED_ZIP_HASH = "2c6b6042b9f2ad55cc6914ee0ae06a97f2e763576e2b2129a596ffe016c364a3"
STARTUP_EXE = "Startup.exe"
# =========================================

def appdata_path():
    appdata = os.getenv("APPDATA")
    return os.path.join(appdata, "Password-Manager")

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def hash_password(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def create_startup_shortcut(exe_path):
    startup = os.path.join(
        os.getenv("APPDATA"),
        "Microsoft\\Windows\\Start Menu\\Programs\\Startup"
    )
    shortcut_path = os.path.join(startup, "PasswordManager.lnk")
    shell = win32com.client.Dispatch("WScript.Shell")
    shortcut = shell.CreateShortCut(shortcut_path)
    shortcut.Targetpath = exe_path
    shortcut.WorkingDirectory = os.path.dirname(exe_path)
    shortcut.save()

def clear_dir(path):
    failed = []
    for name in os.listdir(path):
        full = os.path.join(path, name)
        try:
            if os.path.islink(full) or os.path.isfile(full):
                os.remove(full)
            elif os.path.isdir(full):
                shutil.rmtree(full)
        except Exception:
            if name.lower() == STARTUP_EXE.lower():
                try:
                    subprocess.run(["taskkill", "/f", "/im", STARTUP_EXE], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    time.sleep(0.5)
                    if os.path.islink(full) or os.path.isfile(full):
                        os.remove(full)
                        continue
                    if os.path.isdir(full):
                        shutil.rmtree(full)
                        continue
                except Exception:
                    pass
            failed.append(name)
    return failed

class InstallerGUI:
    def __init__(self):
        self.root = tk.Tk(); self.root.title("Password Manager Installer"); self.root.geometry("500x320"); self.root.resizable(False, False); self.root.configure(bg="#1e1e1e")

        style = ttk.Style()
        style.theme_use("default")
        style.configure("Dark.Horizontal.TProgressbar", troughcolor="#2b2b2b", background="#4caf50", thickness=18)
        style.configure("Dark.TButton", background="#333333", foreground="white")
        style.map("Dark.TButton", background=[("active", "#444444")])

        # ---------- MAIN HEADING ----------
        self.heading = tk.Label(self.root, text="Password-Manager Setup", bg="#1e1e1e", fg="white", font=("Segoe UI", 14, "bold"))
        self.heading.pack(pady=8)

        # ---------- TERMS / T&C FRAME (scrollable) ----------
        self.terms_frame = tk.Frame(self.root, bg="#1e1e1e")
        self.terms_text = tk.Text(self.terms_frame, bg="#121212", fg="#dcdcdc", insertbackground="white", height=10, width=62, wrap="word", relief="flat")
        self.terms_scroll = tk.Scrollbar(self.terms_frame, command=self.terms_text.yview)
        self.terms_text.configure(yscrollcommand=self.terms_scroll.set)
        self.terms_text.grid(row=0, column=0, sticky="nsew", padx=(10,0), pady=6)
        self.terms_scroll.grid(row=0, column=1, sticky="ns", pady=6, padx=(0,10))
        self.terms_frame.grid_rowconfigure(0, weight=1)
        self.terms_frame.grid_columnconfigure(0, weight=1)

        terms_path = os.path.join(getattr(sys, "_MEIPASS", os.path.dirname(__file__)), "terms.txt")
        try:
            with open(terms_path, "r", encoding="utf-8") as tf:
                terms = tf.read()
        except Exception:
            terms = "Terms not found. Please create a terms.txt file in the installer folder."
        self.terms_text.insert("1.0", terms)
        self.terms_text.config(state="disabled")
        self.terms_frame.pack(pady=6)

        self.agree_frame = tk.Frame(self.root, bg="#1e1e1e")
        self.agree_button = ttk.Button(self.agree_frame, text="I Agree", style="Dark.TButton", command=self.on_agree)
        self.cancel_button = ttk.Button(self.agree_frame, text="Cancel", style="Dark.TButton", command=self.root.destroy)
        self.agree_button.grid(row=0, column=0, padx=6)
        self.cancel_button.grid(row=0, column=1, padx=6)
        self.agree_frame.pack(pady=6)

        self.password_frame = tk.Frame(self.root, bg="#1e1e1e")
        self.pw_label = tk.Label(self.password_frame, text="Set Master Password", bg="#1e1e1e", fg="white", font=("Segoe UI", 12, "bold"))
        self.pw_label.pack(pady=6)
        self.pw1 = tk.Entry(self.password_frame, show="*", width=30, bg="#2b2b2b", fg="white", insertbackground="white", relief="flat")
        self.pw1.pack(pady=6, ipady=6)
        self.pw2 = tk.Entry(self.password_frame, show="*", width=30, bg="#2b2b2b", fg="white", insertbackground="white", relief="flat")
        self.pw2.pack(pady=6, ipady=6)
        self.install_button = ttk.Button(self.password_frame, text="Install", style="Dark.TButton", command=self.install)
        self.install_button.pack(pady=12)

        # ---------- DETAILS / LOG FRAME ----------
        self.details_frame = tk.Frame(self.root, bg="#1e1e1e")

        tk.Label(self.details_frame, text="Installation Log", bg="#1e1e1e", fg="white", font=("Segoe UI", 12, "bold")).pack(pady=8)
        self.log_box = tk.Text(self.details_frame, bg="#121212", fg="#dcdcdc", insertbackground="white", height=10, width=60, relief="flat")
        self.log_box.pack(padx=10, pady=5)
        self.log_box.config(state="disabled")
        self.root.mainloop()

    # ---------- HELPERS ----------
    def show_details(self):
        try:
            self.password_frame.pack_forget()
        except Exception:
            pass
        try:
            self.terms_frame.pack_forget()
            self.agree_frame.pack_forget()
        except Exception:
            pass
        self.details_frame.pack(pady=10)

    def on_agree(self):
        try:
            self.terms_frame.pack_forget()
        except Exception:
            pass
        try:
            self.agree_frame.pack_forget()
        except Exception:
            pass
        self.password_frame.pack(pady=10)

    def log(self, msg):
        self.log_box.config(state="normal")
        self.log_box.insert("end", msg + "\n")
        self.log_box.see("end")
        self.log_box.config(state="disabled")
        self.root.update_idletasks()
        self.root.update_idletasks()

    # ---------- INSTALL ----------
    def install(self):
        p1 = self.pw1.get()
        p2 = self.pw2.get()
        if len(p1) < 8:
            messagebox.showerror("Error", "Password must be at least 8 characters")
            return
        if p1 != p2:
            messagebox.showerror("Error", "Passwords do not match")
            return
        try:
            keyring.set_password(SERVICE_NAME, getpass.getuser(), hash_password(p1))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to store master key:\n{e}")
            return
        self.install_button.config(state="disabled")
        self.show_details()

        try:
            self.log("Master password registered 🔐")
            os.makedirs(appdata_path(), exist_ok=True)
            self.log("Application directory ready ✅")
            try:
                target = appdata_path()
                if os.path.exists(target) and os.listdir(target):
                    self.log("Cleaning existing application directory 🧹")
                    failed = clear_dir(target)
                    if failed:
                        self.log("Existing files/folders could not be removed ❌:")
                        for item in failed:
                            self.log(f"  - {item}")
                        self.log("Please delete these manually and re-run the installer ❗")
                        return
                    self.log("Application directory cleaned ✅")
            except Exception as e:
                self.log(f"Warning: failed to clean directory: {e} ⚠️")

            zip_path = os.path.join(appdata_path(), "wow.zip")
            if os.path.exists(zip_path):
                self.log("Existing archive found, verifying ⁉️")
                if sha256_file(zip_path).lower() != EXPECTED_ZIP_HASH.lower():
                    self.log("Cached archive invalid, deleting 🗑️")
                    os.remove(zip_path)
                    self.download_zip(zip_path)
                else:
                    self.log("Cached archive valid, using it 📂")
            else:
                self.download_zip(zip_path)
            self.log("Verifying archive integrity ⁉️")
            if sha256_file(zip_path).lower() != EXPECTED_ZIP_HASH.lower():
                self.log("Hash verification failed ❌")
                os.remove(zip_path)
                return
            self.log("Hash verification passed ✅")
            self.log("Extracting files 📂")
            with zipfile.ZipFile(zip_path, "r") as z:
                z.extractall(appdata_path())
            os.remove(zip_path)
            exe_path = os.path.join(appdata_path(), STARTUP_EXE)
            if not os.path.exists(exe_path):
                self.log("Startup.exe not found after extraction ❌")
                return
            self.log("Creating startup shortcut 🔗")
            create_startup_shortcut(exe_path)
            self.log("Launching Password Manager 🚀")
            os.startfile(exe_path)
            self.log("")
            self.log("Installation Successful ✅")
            tk.Label(self.details_frame, text="Press Ctrl+Shift+L on web/apps for secure logins 🔐", bg="#1e1e1e", fg="#4caf50", font=("Segoe UI", 11, "bold"), justify="center").pack(pady=10)
        except Exception as e:
            self.log(f"❌ Error: {e}")

    def download_zip(self, zip_path):
        self.log("Downloading application files... Please wait ⬇️")
        r = requests.get(ZIP_URL, stream=True)
        r.raise_for_status()
        with open(zip_path, "wb") as f:
            for chunk in r.iter_content(8192):
                if chunk:
                    f.write(chunk)
                    self.root.update_idletasks()

if __name__ == "__main__":
    InstallerGUI()
