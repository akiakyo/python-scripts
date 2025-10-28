#!/usr/bin/env python3
# wifi_vault_elevate.py
# Same Wi-Fi Vault GUI as before but will auto-elevate (UAC) when needed.
# Master password is "akiakyo" (kept as requested).
#
# NOTE: This only prompts for legitimate elevation using Windows UAC.
# It does not bypass protections — if a profile truly hides the key (e.g. Enterprise),
# elevation will not force the password to appear.
 
import os
import sys
import re
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
 
MASTER_PASSWORD = "akiakyo"
 
# ---------------------------
# Elevation helpers
# ---------------------------
def is_admin():
    """Return True if running with admin privileges on Windows."""
    try:
        import ctypes
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False
 
def relaunch_as_admin_and_exit():
    """
    Relaunch the current script with elevation (UAC). If packaged as a frozen exe,
    sys.executable will be the exe; when run with python, sys.executable is the python interpreter
    and sys.argv contains the script path as first element.
    """
    import ctypes
    if os.name != 'nt':
        messagebox.showerror("Not supported", "Elevation/relaunch helper only supports Windows.")
        return False
 
    # Build the command-line arguments (quote each)
    args = ' '.join(f'"{arg}"' for arg in sys.argv)
    try:
        # ShellExecuteW returns >32 for success. Use "runas" to trigger UAC prompt.
        hInstance = ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, args, None, 1)
        # If the call failed it usually returns a value <= 32
        if hInstance <= 32:
            return False
        # Relaunched successfully (UAC dialog shown). We should exit this process.
        return True
    except Exception as e:
        messagebox.showerror("Elevation failed", f"Could not relaunch as administrator:\n{e}")
        return False
 
# If not admin, ask user and relaunch
if os.name == 'nt' and not is_admin():
    # We do this before creating the GUI so the UAC prompt shows early.
    root = tk.Tk()
    root.withdraw()
    resp = messagebox.askyesno("Administrator required",
                               "This tool may require Administrator privileges to show some Wi-Fi keys.\n\n"
                               "Would you like to relaunch as Administrator now? (UAC prompt will appear)")
    root.destroy()
    if resp:
        ok = relaunch_as_admin_and_exit()
        if ok:
            # Terminate the current process — the elevated instance will run separately.
            sys.exit(0)
        else:
            # Either the call failed or user cancelled UAC. Continue but warn user.
            root = tk.Tk()
            root.withdraw()
            messagebox.showwarning("Continuing without admin",
                                   "Continuing without Administrator privileges. Some passwords may remain hidden.")
            root.destroy()
    else:
        # User declined to elevate; continue but warn
        root = tk.Tk()
        root.withdraw()
        messagebox.showinfo("Continuing without admin", "Continuing without Administrator privileges.")
        root.destroy()
 
# ---------------------------
# Netsh helper functions
# ---------------------------
def run(cmd):
    """Run a shell command and return stdout (text). Raises CalledProcessError on failure."""
    return subprocess.check_output(cmd, shell=True, text=True, stderr=subprocess.DEVNULL)
 
def get_current_ssid():
    try:
        out = run('netsh wlan show interfaces')
    except subprocess.CalledProcessError:
        return None
    m = re.search(r'^\s*SSID\s*:\s*(.+)\r?$', out, re.M)
    return m.group(1).strip() if m else None
 
def get_password_for_ssid(ssid):
    try:
        out = run(f'netsh wlan show profile name="{ssid}" key=clear')
    except subprocess.CalledProcessError:
        return None
    m = re.search(r'Key Content\s*:\s*(.+)\r?$', out, re.M)
    return m.group(1).strip() if m else None
 
def list_profiles():
    try:
        out = run('netsh wlan show profiles')
    except subprocess.CalledProcessError:
        return []
    names = re.findall(r'All User Profile\s*:\s*(.+)\r?$', out, re.M)
    return [n.strip() for n in names]
 
def get_password(profile_name):
    try:
        out = run(f'netsh wlan show profile name="{profile_name}" key=clear')
    except subprocess.CalledProcessError:
        return None
    m = re.search(r'Key Content\s*:\s*(.+)\r?$', out, re.M)
    return m.group(1).strip() if m else None
 
# ---------------------------
# GUI
# ---------------------------
class WifiVaultApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Wi-Fi Vault")
        self.resizable(False, False)
        self.geometry("520x420")
        self._build_login()
 
    def _build_login(self):
        for w in self.winfo_children():
            w.destroy()
 
        frm = ttk.Frame(self, padding=20)
        frm.pack(expand=True, fill="both")
 
        ttk.Label(frm, text="Enter master password:", font=("Segoe UI", 11)).pack(pady=(0,8))
        self.pw_var = tk.StringVar()
        ent = ttk.Entry(frm, textvariable=self.pw_var, show="*", width=30)
        ent.pack()
        ent.focus()
 
        btn = ttk.Button(frm, text="Unlock", command=self._check_password)
        btn.pack(pady=12)
 
        hint = ttk.Label(frm, text="(This tool runs local netsh commands to show saved Wi-Fi keys)\n"
                                   "If not elevated, some profiles may hide their keys.",
                         font=("Segoe UI", 8), foreground="gray")
        hint.pack(pady=(8,0))
 
    def _check_password(self):
        if self.pw_var.get() == MASTER_PASSWORD:
            self._build_main()
        else:
            messagebox.showerror("Wrong password", "Incorrect master password.")
 
    def _build_main(self):
        for w in self.winfo_children():
            w.destroy()
 
        top = ttk.Frame(self, padding=10)
        top.pack(fill="x")
        ttk.Label(top, text="Wi-Fi Vault", font=("Segoe UI", 13, "bold")).pack(side="left")
        ttl = ttk.Button(top, text="Lock", command=self._build_login)
        ttl.pack(side="right")
 
        body = ttk.Frame(self, padding=(10,5))
        body.pack(expand=True, fill="both")
 
        btns = ttk.Frame(body)
        btns.pack(fill="x", pady=(0,6))
        ttk.Button(btns, text="Show current SSID & password", command=self.show_current).pack(side="left", padx=(0,6))
        ttk.Button(btns, text="Show all saved profiles", command=self.show_all).pack(side="left", padx=(0,6))
        ttk.Button(btns, text="Save all to CSV", command=self.save_csv).pack(side="left", padx=(6,0))
 
        self.out = tk.Text(body, wrap="none", height=18)
        self.out.pack(expand=True, fill="both")
        self.out.configure(state="disabled", font=("Consolas", 10))
 
        xbar = ttk.Scrollbar(body, orient="horizontal", command=self.out.xview)
        xbar.pack(fill="x")
        ybar = ttk.Scrollbar(body, orient="vertical", command=self.out.yview)
        ybar.pack(side="right", fill="y")
        self.out.configure(xscrollcommand=xbar.set, yscrollcommand=ybar.set)
 
        # Show current privilege level
        priv = "Administrator" if is_admin() else "Standard user"
        self._append(f"Privilege: {priv}")
        self._append("-" * 60)
 
    def _append(self, text):
        self.out.configure(state="normal")
        self.out.insert("end", text + "\n")
        self.out.configure(state="disabled")
        self.out.see("end")
 
    def clear_out(self):
        self.out.configure(state="normal")
        self.out.delete("1.0", "end")
        self.out.configure(state="disabled")
 
    def show_current(self):
        self.clear_out()
        self._append(f"Privilege: {'Administrator' if is_admin() else 'Standard user'}")
        self._append("-" * 60)
        ssid = get_current_ssid()
        if not ssid:
            self._append("Not connected to any Wi-Fi network (or 'netsh' failed).")
            return
        pw = get_password_for_ssid(ssid)
        self._append(f"Current SSID: {ssid}")
        self._append(f"Password    : {pw if pw else '<not available>'}")
 
    def show_all(self):
        self.clear_out()
        self._append(f"Privilege: {'Administrator' if is_admin() else 'Standard user'}")
        self._append("-" * 60)
        profiles = list_profiles()
        if not profiles:
            self._append("No Wi-Fi profiles found (or 'netsh' failed).")
            return
        for p in profiles:
            pw = get_password(p)
            self._append(f"{p} : {pw if pw else '<no password shown>'}")
 
    def save_csv(self):
        profiles = list_profiles()
        if not profiles:
            messagebox.showinfo("No profiles", "No Wi-Fi profiles found to save.")ak
            return
        file = filedialog.asksaveasfilename(defaultextension=".csv",
                                            filetypes=[("CSV files","*.csv"),("All files","*.*")],
                                            title="Save Wi-Fi profiles as CSV")
        if not file:
            return
        try:
            with open(file, "w", encoding="utf-8", newline="") as f:
                f.write("SSID,Password\n")
                for p in profiles:
                    pw = get_password(p) or ""
                    safe_ssid = '"' + p.replace('"','""') + '"'
                    safe_pw = '"' + pw.replace('"','""') + '"'
                    f.write(f"{safe_ssid},{safe_pw}\n")
            messagebox.showinfo("Saved", f"Saved to {file}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save: {e}")
 
if __name__ == "__main__":
    app = WifiVaultApp()
    app.mainloop()
