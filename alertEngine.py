import psutil
import ctypes
import threading
import logging
import tkinter as tk
from datetime import datetime
from typing import Optional
from database import (
    insertIntoActivityLogTable,
    insertIntoAlertTable,
    updateAlertResponse,
    getOrCreateAppID,
)

SCRIPTS_EXT = {'.exe', '.bat', '.cmd', '.ps1', '.vbs', '.js', '.py', '.gs', '.wsf'}

BLOCKLISTED_APPS = {
    #spyglass
    'spyglass.exe', 'spyglass.py',

    # remote access tools
    'teamviewer.exe', 'anydesk.exe', 'logmein.exe', 'ultraviewer.exe', 'ammyy.exe',

    #network sniffers
    'wireshark.exe', 'tcpdump.exe', 'nmap.exe', 'fiddler.exe', 'netsh.exe',

    #Credential harvesting
    'mimikatz.exe', 'hashcat.exe', 'john.exe', 'hydra.exe', 'crunch.exe', 'lazagne.exe',

    #Reverseshells
    'nc.exe', 'netcat.exe', 'ncat.exe', 'socat.exe', 'plink.exe', 'msfvenom.exe',
}

PASSWORD_KEYS = {'password', 'pass', 'sign in', 'login', 'auth', 'credentials', 'authentication'}

LOW_SECURITY = 'low'
MED_SECURITY = 'medium'
HIGH_SECURITY = 'high'
CRITICAL_SECURITY = 'critical'

SEVERITY_TO_LOG_LEVEL = {
    'low': logging.INFO,
    'medium': logging.WARNING,
    'high': logging.ERROR,
    'critical': logging.CRITICAL,
}

SEVERITY_COLOURS = {
    'low': "#2d6a4f",       # dark green
    'medium': "#e76f51",    # orange
    'high': "#d62828",      # red
    'critical': "#6a040e",  # dark red
}


class AlertEngine:
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.is_running = False
        self.baseline_pids = set()
        self.alert_history = {}
        self.scan_thread = None
        self.lock = threading.Lock()
        self.polling_interval = 15  # seconds

    def start(self):
        if self.is_running:
            logging.warning("Alert Engine is already running.")
            return
        logging.info("Setting up Alert Engine with baseline snapshot...")
        self.baseline_pids = {p.pid for p in psutil.process_iter()}
        self.is_running = True
        self.scan_thread = threading.Thread(target=self.scan_loop, daemon=True)
        self.scan_thread.start()

    def stop(self):
        if not self.is_running:
            logging.warning("Alert Engine is not running.")
            return
        logging.info("Stopping Alert Engine...")
        self.is_running = False

    def scan_loop(self):
        #runs checks each polling interval
        while self.is_running:
            self.check_thresholds()
            threading.Event().wait(self.polling_interval)

    # ── threshold checks ──────────────────────────────────────────

    def check_thresholds(self):
        scripts = self.get_running_scripts()
        new_scripts = [s for s in scripts if s['pid'] not in self.baseline_pids]

        #LOW - NON SYSTEM SCRIPTS
        for script in new_scripts:
            self.raise_alert(
                LOW_SECURITY,
                alert_type="Background Script",
                key=f"bg_{script['pid']}",
                message=f"Background script detected: {script['name']} (PID {script['pid']})",
                app_name=script['name'], exe_path=script.get('exe', ''))

        #MEDIUM - 50+ SCRIPTS SIMULTANEOUSLY
        if len(scripts) >= 50:
            self.raise_alert(
                MED_SECURITY,
                alert_type="Excessive Scripts",
                key="script_volume",
                message=f"High number of background scripts detected: {len(scripts)}",
                app_name=None, exe_path=None)

        #HIGH - 10+ SCRIPTS FROM SAME APP
        app_counts = {}
        for script in scripts:
            app_counts.setdefault(script['name'], []).append(script)
        for app, instances in app_counts.items():
            if len(instances) >= 10:
                self.raise_alert(
                    HIGH_SECURITY,
                    alert_type="Suspicious App Behavior",
                    key=f"AppFlood_{app}",
                    message=f"{len(instances)} background scripts from {app} detected",
                    app_name=app, exe_path=instances[0].get('exe', ''))

        #CRITICAL - BLOCKLISTED APPS
        for script in scripts:
            if script['name'].lower() in BLOCKLISTED_APPS:
                self.raise_alert(
                    CRITICAL_SECURITY,
                    alert_type="Blocklisted App Detected",
                    key=f"Blocklist_{script['name']}",
                    message=f"Blocklisted app detected: {script['name']} (PID {script['pid']})",
                    app_name=script['name'], exe_path=script.get('exe', ''))

        #CRITICAL - password fields detected
        for title in self.get_all_window_titles():
            if any(key in title.lower() for key in PASSWORD_KEYS):
                self.raise_alert(
                    CRITICAL_SECURITY,
                    alert_type="Password Field Detected",
                    key=f"PasswordField_{title[:40]}",
                    message=f'Potential password field detected in window: "{title}"',
                    app_name=None, exe_path=None)
                break

    # ── alert dispatcher ──────────────────────────────────────────
    def raise_alert(self, severity: str, alert_type: str, key: str, message: str,
                    app_name: Optional[str] = None, exe_path: Optional[str] = None):
        #Log alert, update DB, show popup
        alert_key = (severity, key)
        if alert_key in self.alert_history:
            return
        self.alert_history[alert_key] = datetime.now()

        log_level = SEVERITY_TO_LOG_LEVEL.get(severity, logging.WARNING)
        logging.getLogger('app').log(log_level, f"[{severity.upper()}] {message}")

        # update DB
        app_id = None
        if app_name and exe_path:
            app_id = getOrCreateAppID(app_name, exe_path)
        alert_id = insertIntoAlertTable(
            userID=self.user_id, alertType=alert_type,
            severity=severity, message=message, appID=app_id)
        if app_id is not None:
            insertIntoActivityLogTable(
                self.user_id, appID=app_id,
                action=f"alert_{alert_type}", category=severity, reason=message)

        # Show popup on a separate thread
        threading.Thread(
            target=self.show_popup,
            args=(severity, message, key, alert_id),
            daemon=True).start()

    # ── Tkinter popup ─────────────────────────────────────────────

    def show_popup(self, severity: str, message: str, key: str,
                   alert_id: Optional[int] = None):
        bg = SEVERITY_COLOURS.get(severity, '#000')
        popup_w, popup_h = 280, 120
        root = tk.Tk()
        root.title(f"SPYGLASS ALERT")
        root.configure(bg=bg)
        root.overrideredirect(True)          # borderless window
        root.attributes("-topmost", True)
        root.attributes("-alpha", 0.75)      # semi-transparent
        screen_w = root.winfo_screenwidth()
        root.geometry(f"{popup_w}x{popup_h}+{screen_w - popup_w - 75}+20")
        root.resizable(False, False)

        # ── title ──
        tk.Label(root, text=f"SPYGLASS ALERT ({severity.upper()})",
                 font=("Segoe UI", 9, "bold"),
                 bg=bg, fg="#ffffff", anchor='w').pack(fill='x', padx=10, pady=(8, 0))

        # ── message ──
        tk.Label(root, text=message.upper(),
                 font=("Segoe UI", 8, "bold"),
                 bg=bg, fg="#ffffff",
                 wraplength=255, justify='left', anchor='nw').pack(fill='both', expand=True, padx=10, pady=(4, 0))

        # ── button bar ──
        btn_frame = tk.Frame(root, bg=bg)
        btn_frame.pack(fill='x', side='bottom')

        def dismiss():
            if alert_id is not None:
                updateAlertResponse(alert_id, 'dismissed')
            root.destroy()

        def resolve():
            if alert_id is not None:
                updateAlertResponse(alert_id, 'resolved')
            with self.lock:
                self.alert_history.pop((severity, key), None)
            root.destroy()

        btn_style = dict(font=("Segoe UI", 8, "bold"), fg="#ffffff",
                         relief='flat', cursor='hand2', pady=4)
        tk.Button(btn_frame, text="DISMISS", command=dismiss,
                  bg="#dad8d8", activebackground="#3e5a6a",
                  **btn_style).pack(side='left', fill='x', expand=True)
        tk.Button(btn_frame, text="RESOLVE", command=resolve,
                  bg="#50B17C", activebackground="#3e5a6a",
                  **btn_style).pack(side='left', fill='x', expand=True)

        root.after(30000, root.destroy)  # auto-close after 30s
        root.mainloop()

    # ── helpers ────────────────────────────────────────────────────

    def get_running_scripts(self):
        scripts = []
        for proc in psutil.process_iter(['pid', 'name', 'exe']):
            try:
                info = proc.info
                name = (info.get('name') or '').lower()
                if any(name.endswith(ext) for ext in SCRIPTS_EXT):
                    scripts.append({
                        'pid': info['pid'],
                        'name': info.get('name', ''),
                        'exe': info.get('exe') or '',
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return scripts

    def get_all_window_titles(self):
        titles = []
        if not hasattr(ctypes, 'windll'):
            return titles

        def enum_cb(hwnd, _):
            length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
            if length > 0:
                buf = ctypes.create_unicode_buffer(length + 1)
                ctypes.windll.user32.GetWindowTextW(hwnd, buf, length + 1)
                if buf.value:
                    titles.append(buf.value)
            return True

        WNDENUMPROC = ctypes.WINFUNCTYPE(
            ctypes.c_bool, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int))
        ctypes.windll.user32.EnumWindows(WNDENUMPROC(enum_cb), 0)
        return titles
        